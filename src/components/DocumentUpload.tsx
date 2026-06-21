import { CheckCircle2, FileUp, LoaderCircle, ShieldCheck } from "lucide-react";
import { useId, useState } from "react";
import { api, ApiError } from "../api";

export function DocumentUpload({
  documentType,
  onExtracted,
}: {
  documentType: string;
  onExtracted: (fields: Record<string, unknown>) => void;
}) {
  const inputId = useId();
  const consentId = useId();
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const extract = async () => {
    if (!file || !consent) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const upload = await api.uploadDocument(file);
      const result = await api.extractDocument(
        upload.upload_token,
        documentType,
      );
      onExtracted(result.extraction.fields);
      setSuccess(
        `Fields extracted from ${upload.filename}. Review them below before analysis.`,
      );
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "This document could not be extracted.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="document-upload">
      <div className="upload-heading">
        <span className="upload-icon">
          <FileUp />
        </span>
        <div>
          <strong>Extract from a real document</strong>
          <p>PDF, JPEG, PNG, or WebP · maximum 10 MB</p>
        </div>
      </div>
      <label className="file-picker" htmlFor={inputId}>
        <span>{file ? file.name : "Choose a document"}</span>
        <em>{file ? "Choose another" : "Browse file"}</em>
        <input
          id={inputId}
          type="file"
          accept="application/pdf,image/jpeg,image/png,image/webp"
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
            setError(null);
            setSuccess(null);
          }}
        />
      </label>
      <label className="consent-check" htmlFor={consentId}>
        <input
          id={consentId}
          type="checkbox"
          checked={consent}
          onChange={(event) => setConsent(event.target.checked)}
        />
        <span>
          I understand this document will be sent to Google Gemini for field
          extraction. The temporary local upload is deleted after processing.
        </span>
      </label>
      <button
        type="button"
        className="button button-upload"
        disabled={!file || !consent || loading}
        onClick={() => void extract()}
      >
        {loading ? (
          <>
            <LoaderCircle className="spin" /> Extracting fields…
          </>
        ) : (
          <>
            <ShieldCheck /> Extract document fields
          </>
        )}
      </button>
      {error && <p className="upload-message upload-error">{error}</p>}
      {success && (
        <p className="upload-message upload-success">
          <CheckCircle2 /> {success}
        </p>
      )}
    </div>
  );
}
