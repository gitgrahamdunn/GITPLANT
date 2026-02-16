interface SkeletonProps {
  lines?: number;
}

export default function Skeleton({ lines = 3 }: SkeletonProps): JSX.Element {
  return (
    <div className="skeleton-wrap" aria-hidden="true">
      {Array.from({ length: lines }).map((_, index) => (
        <div key={index} className="skeleton-line" />
      ))}
    </div>
  );
}
