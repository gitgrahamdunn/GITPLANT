interface BannerProps {
  tone: "error" | "success" | "info";
  message: string;
}

export default function Banner({ tone, message }: BannerProps): JSX.Element {
  return <p className={`banner banner-${tone}`}>{message}</p>;
}
