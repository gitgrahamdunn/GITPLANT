use std::{fs, path::{Path, PathBuf}};
use chrono::Utc;
use rusqlite::{params, Connection};
use serde::Serialize;
use tauri::Manager;
use uuid::Uuid;

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct ImportedDocumentPayload {
    document_id: String,
    title: String,
    managed_file_path: String,
    file_size_bytes: u64,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RecentDocumentView {
    document_id: String,
    title: String,
    managed_file_path: String,
    opened_at: String,
    page_count: Option<i64>,
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
          source_path TEXT,
          page_count INTEGER,
          file_size_bytes INTEGER NOT NULL,
          imported_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id)
        );
        CREATE TABLE IF NOT EXISTS recent_documents (
          id TEXT PRIMARY KEY,
          document_id TEXT NOT NULL,
          opened_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id)
        );
        "
    )?;
    Ok(())
}

fn open_conn<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> anyhow::Result<Connection> {
    let conn = Connection::open(db_path(app)?)?;
    init_schema(&conn)?;
    Ok(conn)
}

#[tauri::command]
fn import_pdf_from_picker<R: tauri::Runtime>(app: tauri::AppHandle<R>) -> Result<ImportedDocumentPayload, String> {
    let selected = rfd::FileDialog::new().add_filter("PDF", &["pdf"]).pick_file().ok_or("No file selected")?;
    if selected.extension().and_then(|e| e.to_str()).map(|s| s.to_lowercase()) != Some("pdf".into()) {
        return Err("Invalid file type. Please select a PDF.".into());
    }
    let doc_id = Uuid::new_v4().to_string();
    let rev_id = Uuid::new_v4().to_string();
    let now = Utc::now().to_rfc3339();
    let name = selected.file_stem().and_then(|s| s.to_str()).unwrap_or("Untitled").to_string();
    let file_name = selected.file_name().and_then(|s| s.to_str()).unwrap_or("document.pdf").to_string();
    let managed_path = storage_dir(&app).map_err(|e| e.to_string())?.join(format!("{}-{}", doc_id, file_name));
    fs::copy(&selected, &managed_path).map_err(|e| format!("Import failure: {e}"))?;
    let file_size = fs::metadata(&managed_path).map_err(|e| e.to_string())?.len();

    let conn = open_conn(&app).map_err(|e| format!("DB initialization failure: {e}"))?;
    conn.execute("INSERT INTO documents (id, title, created_at, updated_at) VALUES (?1, ?2, ?3, ?3)", params![doc_id, name, now]).map_err(|e| e.to_string())?;
    conn.execute("INSERT INTO document_revisions (id, document_id, revision_number, managed_file_path, original_file_name, source_path, page_count, file_size_bytes, imported_at) VALUES (?1, ?2, 1, ?3, ?4, ?5, NULL, ?6, ?7)",
      params![rev_id, doc_id, managed_path.to_string_lossy().to_string(), file_name, selected.to_string_lossy().to_string(), file_size as i64, now]).map_err(|e| e.to_string())?;
    conn.execute("INSERT INTO recent_documents (id, document_id, opened_at) VALUES (?1, ?2, ?3)", params![Uuid::new_v4().to_string(), doc_id, now]).map_err(|e| e.to_string())?;

    Ok(ImportedDocumentPayload { document_id: doc_id, title: name, managed_file_path: managed_path.to_string_lossy().to_string(), file_size_bytes: file_size })
}

#[tauri::command]
fn list_recent_documents<R: tauri::Runtime>(app: tauri::AppHandle<R>) -> Result<Vec<RecentDocumentView>, String> {
    let conn = open_conn(&app).map_err(|e| e.to_string())?;
    let mut stmt = conn.prepare("SELECT d.id,d.title,dr.managed_file_path,r.opened_at,dr.page_count FROM recent_documents r JOIN documents d ON d.id=r.document_id JOIN document_revisions dr ON dr.document_id=d.id ORDER BY r.opened_at DESC LIMIT 20").map_err(|e| e.to_string())?;
    let rows = stmt.query_map([], |row| Ok(RecentDocumentView {
        document_id: row.get(0)?, title: row.get(1)?, managed_file_path: row.get(2)?, opened_at: row.get(3)?, page_count: row.get(4)?
    })).map_err(|e| e.to_string())?;
    Ok(rows.filter_map(Result::ok).collect())
}

fn latest_path(conn: &Connection, document_id: &str) -> Result<(String, String), String> {
    conn.query_row("SELECT d.title,dr.managed_file_path FROM documents d JOIN document_revisions dr ON dr.document_id=d.id WHERE d.id=?1 ORDER BY dr.revision_number DESC LIMIT 1", params![document_id], |r| Ok((r.get(0)?, r.get(1)?))).map_err(|e| e.to_string())
}

#[tauri::command]
fn open_document<R: tauri::Runtime>(app: tauri::AppHandle<R>, document_id: String) -> Result<ImportedDocumentPayload, String> {
    let conn = open_conn(&app).map_err(|e| e.to_string())?;
    let (title, managed_file_path) = latest_path(&conn, &document_id)?;
    conn.execute("INSERT INTO recent_documents (id, document_id, opened_at) VALUES (?1, ?2, ?3)", params![Uuid::new_v4().to_string(), document_id, Utc::now().to_rfc3339()]).map_err(|e| e.to_string())?;
    let file_size_bytes = fs::metadata(&managed_file_path).map_err(|e| e.to_string())?.len();
    Ok(ImportedDocumentPayload { document_id, title, managed_file_path, file_size_bytes })
}

#[tauri::command]
fn read_document_bytes<R: tauri::Runtime>(app: tauri::AppHandle<R>, document_id: String) -> Result<Vec<u8>, String> {
    let conn = open_conn(&app).map_err(|e| e.to_string())?;
    let (_, managed_file_path) = latest_path(&conn, &document_id)?;
    fs::read(Path::new(&managed_file_path)).map_err(|e| e.to_string())
}

#[tauri::command]
fn update_page_count<R: tauri::Runtime>(app: tauri::AppHandle<R>, document_id: String, page_count: i64) -> Result<(), String> {
    let conn = open_conn(&app).map_err(|e| e.to_string())?;
    conn.execute("UPDATE document_revisions SET page_count=?1 WHERE document_id=?2 AND revision_number=1", params![page_count, document_id]).map_err(|e| e.to_string())?;
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![import_pdf_from_picker, list_recent_documents, open_document, read_document_bytes, update_page_count])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sqlite_schema_supports_document_and_recent_persistence() {
        let conn = Connection::open_in_memory().unwrap();
        init_schema(&conn).unwrap();
        conn.execute("INSERT INTO documents (id,title,created_at,updated_at) VALUES ('d1','Doc','t','t')", []).unwrap();
        conn.execute("INSERT INTO document_revisions (id,document_id,revision_number,managed_file_path,original_file_name,source_path,page_count,file_size_bytes,imported_at) VALUES ('r1','d1',1,'/tmp/a.pdf','a.pdf','/src/a.pdf',3,99,'t')", []).unwrap();
        conn.execute("INSERT INTO recent_documents (id,document_id,opened_at) VALUES ('x','d1','t')", []).unwrap();
        let mut stmt = conn.prepare("SELECT COUNT(*) FROM recent_documents").unwrap();
        let count: i64 = stmt.query_row([], |r| r.get(0)).unwrap();
        assert_eq!(count, 1);
    }
}
