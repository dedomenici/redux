import { useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";

const DEST = "https://dedomenici.github.io/themound";

export const Route = createFileRoute("/themound")({
  head: () => ({
    meta: [
      { title: "The Mound has moved" },
      { httpEquiv: "refresh", content: `0; url=${DEST}/` },
    ],
  }),
  component: RedirectTheMound,
});

function moundDestination() {
  const path = window.location.pathname;
  const rest = path.replace(/^(?:\/redux)?\/themound/, "") || "/";
  return DEST + (rest.startsWith("/") ? rest : `/${rest}`) + window.location.search + window.location.hash;
}

function RedirectTheMound() {
  useEffect(() => {
    window.location.replace(moundDestination());
  }, []);
  const href = typeof window === "undefined" ? `${DEST}/` : moundDestination();
  return (
    <p style={{ padding: "2rem", fontFamily: "Outfit, sans-serif" }}>
      The Mound has moved to{" "}
      <a href={href}>{DEST}/</a>.
    </p>
  );
}
