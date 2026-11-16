import { useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";

const DEST = "https://dedomenici.github.io/themound/";

export const Route = createFileRoute("/mound")({
  head: () => ({
    meta: [{ title: "The Mound has moved" }, { httpEquiv: "refresh", content: `0; url=${DEST}` }],
  }),
  component: function RedirectMound() {
    useEffect(() => {
      window.location.replace(DEST + window.location.search + window.location.hash);
    }, []);
    return (
      <p style={{ padding: "2rem", fontFamily: "Outfit, sans-serif" }}>
        The Mound has moved to <a href={DEST}>{DEST}</a>.
      </p>
    );
  },
});
