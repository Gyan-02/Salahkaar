import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { DocumentUpload } from "../components/DocumentUpload";

it("uploads with consent and returns editable extracted fields", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        upload_token: "upload-1",
        filename: "land.pdf",
        content_type: "application/pdf",
      }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        extraction: {
          document_type: "land_record",
          fields: { owner_name: "Ravi Kumar" },
          extractor: "gemini:gemini-2.5-flash",
          status: "SUCCEEDED",
          fallback_used: false,
          failure_reason: null,
        },
        document: {},
      }),
    });
  vi.stubGlobal("fetch", fetchMock);
  const onExtracted = vi.fn();
  render(
    <DocumentUpload documentType="land_record" onExtracted={onExtracted} />,
  );

  const file = new File(["pdf"], "land.pdf", { type: "application/pdf" });
  fireEvent.change(screen.getByLabelText(/choose a document/i), {
    target: { files: [file] },
  });
  fireEvent.click(screen.getByLabelText(/sent to Google Gemini/i));
  fireEvent.click(
    screen.getByRole("button", { name: /extract document fields/i }),
  );

  await waitFor(() =>
    expect(onExtracted).toHaveBeenCalledWith({ owner_name: "Ravi Kumar" }),
  );
  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(fetchMock.mock.calls[0][1].body).toBeInstanceOf(FormData);
  expect(JSON.parse(String(fetchMock.mock.calls[1][1].body))).toMatchObject({
    upload_token: "upload-1",
    document_type: "land_record",
    consent_to_external_processing: true,
  });
  expect(
    screen.getByText(/review them below before analysis/i),
  ).toBeInTheDocument();
});
