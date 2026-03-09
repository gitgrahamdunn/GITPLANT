use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
};

use anyhow::anyhow;
use chrono::Utc;
use lopdf::Document as LoDocument;
use rusqlite::{params, Connection};
use serde::Serialize;
use tauri::Manager;
use uuid::Uuid;

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct ImportedDocumentPayload {
    document_id: String,
    revision_id: String,
    title: String,
    managed_file_path: String,
    file_size_bytes: u64,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct DerivedRevisionPayload {
    document_id: String,
    source_revision_id: String,
    derived_revision_id: String,
    managed_file_path: String,
    page_count: i64,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RecentDocumentView {
    document_id: String,
    title: String,
    managed_file_path: String,
    opened_at: String,
    page_count: Option<i64>,
    active_revision_id: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct ProcessingJobRecord {
    id: String,
    revision_id: String,
    job_type: String,
    status: String,
    payload_json: Option<String>,
    error_message: Option<String>,
    created_at: String,
    started_at: Option<String>,
    completed_at: Option<String>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct ExtractedPageTextRecord {
    id: String,
    revision_id: String,
    page_number: i64,
    text_content: String,
    extracted_at: String,
}

fn db_path<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> anyhow::Result<PathBuf> {
    let dir = app.path().app_data_dir()?;
    fs::create_dir_all(&dir)?;
    Ok(dir.join("gitplant.db"))
}

fn storage_dir<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> anyhow::Result<PathBuf> {
    let dir = app.path().app_data_dir()?.join("documents");
    fs::create_dir_all(&dir)?;
    Ok(dir)
}

fn init_schema(conn: &Connection) -> anyhow::Result<()> {
    conn.execute_batch(
        "
        CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS document_revisions (
          id TEXT PRIMARY KEY,
          document_id TEXT NOT NULL,
          revision_number INTEGER NOT NULL,
          managed_file_path TEXT NOT NULL,
          original_file_name TEXT NOT NULL,
          page_count INTEGER,
          file_size_bytes INTEGER NOT NULL,
          imported_at TEXT NOT NULL,
          source_revision_id TEXT,
          derivation_type TEXT,
          FOREIGN KEY(document_id) REFERENCES documents(id),
          FOREIGN KEY(source_revision_id) REFERENCES document_revisions(id)
        );
        CREATE TABLE IF NOT EXISTS recent_documents (
          id TEXT PRIMARY KEY,
          document_id TEXT NOT NULL,
          opened_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id)
        );
        CREATE TABLE IF NOT EXISTS processing_jobs (
          id TEXT PRIMARY KEY,
          revision_id TEXT NOT NULL,
          job_type TEXT NOT NULL,
          status TEXT NOT NULL,
          payload_json TEXT,
          error_message TEXT,
          created_at TEXT NOT NULL,
          started_at TEXT,
          completed_at TEXT,
          FOREIGN KEY(revision_id) REFERENCES document_revisions(id)
        );
        CREATE TABLE IF NOT EXISTS extracted_page_text (
          id TEXT PRIMARY KEY,
          revision_id TEXT NOT NULL,
          page_number INTEGER NOT NULL,
          text_content TEXT NOT NULL,
          extracted_at TEXT NOT NULL,
          FOREIGN KEY(revision_id) REFERENCES document_revisions(id)
        );
        CREATE TABLE IF NOT EXISTS audit_events (
          id TEXT PRIMARY KEY,
          entity_type TEXT NOT NULL,
          entity_id TEXT NOT NULL,
          event_type TEXT NOT NULL,
          payload_json TEXT,
          occurred_at TEXT NOT NULL
        );
        ",
    )?;
    Ok(())
}

fn open_conn<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> anyhow::Result<Connection> {
    let conn = Connection::open(db_path(app)?)?;
    init_schema(&conn)?;
    Ok(conn)
}

fn insert_audit_event(
    conn: &Connection,
    entity_type: &str,
    entity_id: &str,
    event_type: &str,
    payload_json: Option<String>,
) -> anyhow::Result<()> {
    conn.execute(
        "INSERT INTO audit_events (id,entity_type,entity_id,event_type,payload_json,occurred_at) VALUES (?1,?2,?3,?4,?5,?6)",
        params![
            Uuid::new_v4().to_string(),
            entity_type,
            entity_id,
            event_type,
            payload_json,
            Utc::now().to_rfc3339()
        ],
    )?;
    Ok(())
}

fn latest_revision_for_document(conn: &Connection, document_id: &str) -> Result<(String, String, String), String> {
    conn.query_row(
        "SELECT d.title,dr.managed_file_path,dr.id FROM documents d JOIN document_revisions dr ON dr.document_id=d.id WHERE d.id=?1 ORDER BY dr.revision_number DESC LIMIT 1",
        params![document_id],
        |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
    )
    .map_err(|e| e.to_string())
}

fn revision_row(conn: &Connection, revision_id: &str) -> Result<(String, String, String), String> {
    conn.query_row(
        "SELECT document_id, managed_file_path, original_file_name FROM document_revisions WHERE id=?1",
        params![revision_id],
        |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
    )
    .map_err(|e| e.to_string())
}

fn extract_pages(source_path: &str, start_page: u32, end_page: u32, output_path: &Path) -> anyhow::Result<usize> {
    let mut source = LoDocument::load(source_path)?;
    let pages: BTreeMap<u32, lopdf::ObjectId> = source.get_pages();
    let keep: Vec<u32> = pages
        .keys()
        .copied()
        .filter(|p| *p >= start_page && *p <= end_page)
        .collect();
    if keep.is_empty() {
        return Err(anyhow!("No pages in selected range"));
    }
    source.extract_pages(&keep);
    source.prune_objects();
    source.save(output_path)?;
    Ok(keep.len())
}

#[tauri::command]
fn import_pdf_from_picker<R: tauri::Runtime>(app: tauri::AppHandle<R>) -> Result<ImportedDocumentPayload, String> {
    let selected = rfd::FileDialog::new()
        .add_filter("PDF", &["pdf"])
        .pick_file()
        .ok_or("No file selected")?;
    if selected
        .extension()
        .and_then(|e| e.to_str())
        .map(|s| s.to_lowercase())
        != Some("pdf".into())
    {
        return Err("Invalid file type. Please select a PDF.".into());
    }

    let doc_id = Uuid::new_v4().to_string();
    let rev_id = Uuid::new_v4().to_string();
    let now = Utc::now().to_rfc3339();
    let name = selected
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("Untitled")
        .to_string();
    let file_name = selected
        .file_name()
        .and_then(|s| s.to_str())
        .unwrap_or("document.pdf")
        .to_string();
    let managed_path = storage_dir(&app)
        .map_err(|e| e.to_string())?
        .join(format!("{}-{}", doc_id, file_name));
    fs::copy(&selected, &managed_path).map_err(|e| format!("Import failure: {e}"))?;
    let file_size = fs::metadata(&managed_path).map_err(|e| e.to_string())?.len();

    let conn = open_conn(&app).map_err(|e| format!("DB initialization failure: {e}"))?;
    conn.execute(
        "INSERT INTO documents (id, title, created_at, updated_at) VALUES (?1, ?2, ?3, ?3)",
        params![doc_id, name, now],
    )
    .map_err(|e| e.to_string())?;
    conn.execute(
      "INSERT INTO document_revisions (id, document_id, revision_number, managed_file_path, original_file_name, page_count, file_size_bytes, imported_at, source_revision_id, derivation_type) VALUES (?1, ?2, 1, ?3, ?4, NULL, ?5, ?6, NULL, 'imported_original')",
      params![rev_id, doc_id, managed_path.to_string_lossy().to_string(), file_name, file_size as i64, now],
    ).map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO recent_documents (id, document_id, opened_at) VALUES (?1, ?2, ?3)",
        params![Uuid::new_v4().to_string(), doc_id, now],
    )
    .map_err(|e| e.to_string())?;
    insert_audit_event(
        &conn,
        "document_revision",
        &rev_id,
        "document_revision.imported",
        None,
    )
    .map_err(|e| e.to_string())?;

    Ok(ImportedDocumentPayload {
        document_id: doc_id,
        revision_id: rev_id,
        title: name,
        managed_file_path: managed_path.to_string_lossy().to_string(),
        file_size_bytes: file_size,
    })
}

#[tauri::command]
fn list_recent_documents<R: tauri::Runtime>(app: tauri::AppHandle<R>) -> Result<Vec<RecentDocumentView>, String> {
    let conn = open_conn(&app).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare("SELECT d.id,d.title,dr.managed_file_path,r.opened_at,dr.page_count,dr.id FROM recent_documents r JOIN documents d ON d.id=r.document_id JOIN document_revisions dr ON dr.document_id=d.id AND dr.revision_number=(SELECT MAX(revision_number) FROM document_revisions drr WHERE drr.document_id=d.id) ORDER BY r.opened_at DESC LIMIT 20")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok(RecentDocumentView {
                document_id: row.get(0)?,
                title: row.get(1)?,
                managed_file_path: row.get(2)?,
                opened_at: row.get(3)?,
                page_count: row.get(4)?,
                active_revision_id: row.get(5)?,
            })
        })
        .map_err(|e| e.to_string())?;
    Ok(rows.filter_map(Result::ok).collect())
}

#[tauri::command]
fn open_document<R: tauri::Runtime>(app: tauri::AppHandle<R>, document_id: String) -> Result<ImportedDocumentPayload, String> {
    let conn = open_conn(&app).map_err(|e| e.to_string())?;
    let (title, managed_file_path, revision_id) = latest_revision_for_document(&conn, &document_id)?;
    conn.execute(
        "INSERT INTO recent_documents (id, document_id, opened_at) VALUES (?1, ?2, ?3)",
        params![Uuid::new_v4().to_string(), document_id, Utc::now().to_rfc3339()],
    )
    .map_err(|e| e.to_string())?;
    let file_size_bytes = fs::metadata(&managed_file_path)
        .map_err(|e| e.to_string())?
        .len();
    Ok(ImportedDocumentPayload {
        document_id,
        revision_id,
        title,
        managed_file_path,
        file_size_bytes,
    })
}

#[tauri::command]
fn read_document_bytes<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    document_id: String,
    revision_id: Option<String>,
) -> Result<Vec<u8>, String> {
    let conn = open_conn(&app).map_err(|e| e.to_string())?;
    let managed_file_path = if let Some(target_revision) = revision_id {
        let (_, path, _) = revision_row(&conn, &target_revision)?;
        path
    } else {
        let (_, path, _) = latest_revision_for_document(&conn, &document_id)?;
        path
    };
    fs::read(Path::new(&managed_file_path)).map_err(|e| e.to_string())
}

#[tauri::command]
fn update_page_count<R: tauri::Runtime>(app: tauri::AppHandle<R>, revision_id: String, page_count: i64) -> Result<(), String> {
    let conn = open_conn(&app).map_err(|e| e.to_string())?;
    conn.execute(
        "UPDATE document_revisions SET page_count=?1 WHERE id=?2",
        params![page_count, revision_id],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn extract_pages_to_derived_revision<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    revision_id: String,
    start_page: u32,
    end_page: u32,
) -> Result<DerivedRevisionPayload, String> {
    let conn = open_conn(&app).map_err(|e| e.to_string())?;
    let (document_id, source_path, original_name) = revision_row(&conn, &revision_id)?;
    let next_revision_number: i64 = conn
        .query_row(
            "SELECT COALESCE(MAX(revision_number),0) + 1 FROM document_revisions WHERE document_id=?1",
            params![document_id],
            |r| r.get(0),
        )
        .map_err(|e| e.to_string())?;

    let derived_revision_id = Uuid::new_v4().to_string();
    let out_name = format!("{}-derived-{}", derived_revision_id, original_name);
    let output_path = storage_dir(&app)
        .map_err(|e| e.to_string())?
        .join(out_name);

    insert_audit_event(
        &conn,
        "document_transformation",
        &derived_revision_id,
        "transformation.extract_pages.requested",
        Some(format!(
            "{{\"sourceRevisionId\":\"{}\",\"startPage\":{},\"endPage\":{}}}",
            revision_id, start_page, end_page
        )),
    )
    .map_err(|e| e.to_string())?;

    let page_count = extract_pages(&source_path, start_page, end_page, &output_path).map_err(|e| e.to_string())? as i64;
    let file_size = fs::metadata(&output_path).map_err(|e| e.to_string())?.len() as i64;

    conn.execute(
        "INSERT INTO document_revisions (id, document_id, revision_number, managed_file_path, original_file_name, page_count, file_size_bytes, imported_at, source_revision_id, derivation_type) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, 'extract_pages')",
        params![derived_revision_id, document_id, next_revision_number, output_path.to_string_lossy().to_string(), original_name, page_count, file_size, Utc::now().to_rfc3339(), revision_id],
    )
    .map_err(|e| e.to_string())?;

    insert_audit_event(
        &conn,
        "document_transformation",
        &derived_revision_id,
        "transformation.extract_pages.completed",
        Some(format!("{{\"pageCount\":{}}}", page_count)),
    )
    .map_err(|e| e.to_string())?;

    Ok(DerivedRevisionPayload {
        document_id,
        source_revision_id: revision_id,
        derived_revision_id,
        managed_file_path: output_path.to_string_lossy().to_string(),
        page_count,
    })
}

#[tauri::command]
fn trigger_text_extraction<R: tauri::Runtime>(app: tauri::AppHandle<R>, revision_id: String) -> Result<ProcessingJobRecord, String> {
    let conn = open_conn(&app).map_err(|e| e.to_string())?;
    let (_, source_path, _) = revision_row(&conn, &revision_id)?;
    let now = Utc::now().to_rfc3339();
    let job_id = Uuid::new_v4().to_string();
    conn.execute(
        "INSERT INTO processing_jobs (id,revision_id,job_type,status,payload_json,error_message,created_at,started_at,completed_at) VALUES (?1,?2,'text_extraction','running',NULL,NULL,?3,?3,NULL)",
        params![job_id, revision_id, now],
    )
    .map_err(|e| e.to_string())?;
    conn.execute("DELETE FROM extracted_page_text WHERE revision_id=?1", params![revision_id])
        .map_err(|e| e.to_string())?;

    let extraction = (|| -> anyhow::Result<()> {
        let doc = LoDocument::load(&source_path)?;
        let pages = doc.get_pages();
        for page_num in pages.keys() {
            let text = doc.extract_text(&[*page_num]).unwrap_or_default();
            conn.execute(
                "INSERT INTO extracted_page_text (id,revision_id,page_number,text_content,extracted_at) VALUES (?1,?2,?3,?4,?5)",
                params![Uuid::new_v4().to_string(), revision_id, *page_num as i64, text, Utc::now().to_rfc3339()],
            )?;
        }
        Ok(())
    })();

    match extraction {
        Ok(()) => {
            let done = Utc::now().to_rfc3339();
            conn.execute(
                "UPDATE processing_jobs SET status='completed', completed_at=?1 WHERE id=?2",
                params![done, job_id],
            )
            .map_err(|e| e.to_string())?;
            insert_audit_event(
                &conn,
                "processing_job",
                &job_id,
                "processing.text_extraction.completed",
                None,
            )
            .map_err(|e| e.to_string())?;
            Ok(ProcessingJobRecord {
                id: job_id,
                revision_id,
                job_type: "text_extraction".into(),
                status: "completed".into(),
                payload_json: None,
                error_message: None,
                created_at: now.clone(),
                started_at: Some(now),
                completed_at: Some(done),
            })
        }
        Err(err) => {
            let done = Utc::now().to_rfc3339();
            let error_message = err.to_string();
            conn.execute(
                "UPDATE processing_jobs SET status='failed', completed_at=?1, error_message=?2 WHERE id=?3",
                params![done, error_message, job_id],
            )
            .map_err(|e| e.to_string())?;
            Err(error_message)
        }
    }
}

#[tauri::command]
fn list_extracted_page_text<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    revision_id: String,
) -> Result<Vec<ExtractedPageTextRecord>, String> {
    let conn = open_conn(&app).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare("SELECT id,revision_id,page_number,text_content,extracted_at FROM extracted_page_text WHERE revision_id=?1 ORDER BY page_number")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map(params![revision_id], |r| {
            Ok(ExtractedPageTextRecord {
                id: r.get(0)?,
                revision_id: r.get(1)?,
                page_number: r.get(2)?,
                text_content: r.get(3)?,
                extracted_at: r.get(4)?,
            })
        })
        .map_err(|e| e.to_string())?;
    Ok(rows.filter_map(Result::ok).collect())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            import_pdf_from_picker,
            list_recent_documents,
            open_document,
            read_document_bytes,
            update_page_count,
            extract_pages_to_derived_revision,
            trigger_text_extraction,
            list_extracted_page_text
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sqlite_schema_supports_new_architecture_entities() {
        let conn = Connection::open_in_memory().unwrap();
        init_schema(&conn).unwrap();
        conn.execute(
            "INSERT INTO documents (id,title,created_at,updated_at) VALUES ('d1','Doc','t','t')",
            [],
        )
        .unwrap();
        conn.execute("INSERT INTO document_revisions (id,document_id,revision_number,managed_file_path,original_file_name,page_count,file_size_bytes,imported_at,source_revision_id,derivation_type) VALUES ('r1','d1',1,'/tmp/a.pdf','a.pdf',3,99,'t',NULL,'imported_original')", [])
            .unwrap();
        conn.execute("INSERT INTO document_revisions (id,document_id,revision_number,managed_file_path,original_file_name,page_count,file_size_bytes,imported_at,source_revision_id,derivation_type) VALUES ('r2','d1',2,'/tmp/b.pdf','a.pdf',1,25,'t','r1','extract_pages')", [])
            .unwrap();
        conn.execute("INSERT INTO processing_jobs (id,revision_id,job_type,status,payload_json,error_message,created_at,started_at,completed_at) VALUES ('j1','r2','text_extraction','completed',NULL,NULL,'t','t','t')", [])
            .unwrap();
        conn.execute("INSERT INTO extracted_page_text (id,revision_id,page_number,text_content,extracted_at) VALUES ('e1','r2',1,'hello','t')", [])
            .unwrap();
        let rel: String = conn
            .query_row(
                "SELECT source_revision_id FROM document_revisions WHERE id='r2'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(rel, "r1");
    }

    #[test]
    fn extract_pages_creates_output_pdf() {
        let dir = tempfile::tempdir().unwrap();
        let source = dir.path().join("source.pdf");
        let output = dir.path().join("out.pdf");
        fs::write(
            &source,
            b"%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >> endobj
4 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >> endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000060 00000 n 
0000000130 00000 n 
0000000190 00000 n 
trailer << /Root 1 0 R /Size 5 >>
startxref
250
%%EOF",
        )
        .unwrap();

        let count = extract_pages(source.to_str().unwrap(), 1, 1, &output).unwrap();
        assert_eq!(count, 1);
        assert!(output.exists());
    }

    #[test]
    fn processing_and_text_tables_support_status_updates() {
        let conn = Connection::open_in_memory().unwrap();
        init_schema(&conn).unwrap();
        conn.execute("INSERT INTO documents (id,title,created_at,updated_at) VALUES ('d1','Doc','t','t')",[]).unwrap();
        conn.execute("INSERT INTO document_revisions (id,document_id,revision_number,managed_file_path,original_file_name,page_count,file_size_bytes,imported_at,source_revision_id,derivation_type) VALUES ('r1','d1',1,'/tmp/a.pdf','a.pdf',1,1,'t',NULL,'imported_original')",[]).unwrap();
        conn.execute("INSERT INTO processing_jobs (id,revision_id,job_type,status,payload_json,error_message,created_at,started_at,completed_at) VALUES ('j1','r1','ocr','pending',NULL,NULL,'t',NULL,NULL)",[]).unwrap();
        conn.execute("UPDATE processing_jobs SET status='running', started_at='t2' WHERE id='j1'",[]).unwrap();
        conn.execute("INSERT INTO extracted_page_text (id,revision_id,page_number,text_content,extracted_at) VALUES ('x1','r1',1,'abc','t3')",[]).unwrap();
        let status: String = conn.query_row("SELECT status FROM processing_jobs WHERE id='j1'", [], |r| r.get(0)).unwrap();
        assert_eq!(status, "running");
    }

}
