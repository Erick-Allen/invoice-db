import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import type { Content } from "@tiptap/core";
import { useEffect, useRef, useState } from "react";
import {
    createDocument,
    deleteDocument,
    listDocuments,
    updateDocument,
    type BusinessDocument,
    type DocumentContent,
} from "../api/documents";

const emptyDocumentContent: DocumentContent = {
    type: "doc",
    content: [
        {
            type: "paragraph",
        },
    ],
};

function formatUpdatedAt(value: string) {
    return new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
    }).format(new Date(value));
}

function documentPreview(document: BusinessDocument) {
    return document.content_text || "No document body yet.";
}

export function DocumentsPage() {
    const [documents, setDocuments] = useState<BusinessDocument[]>([]);
    const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [title, setTitle] = useState("");
    const [category, setCategory] = useState("General");
    const [contentJson, setContentJson] = useState<DocumentContent>(emptyDocumentContent);
    const [isEditing, setIsEditing] = useState(false);
    const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const isApplyingEditorContent = useRef(false);

    const isNewDocument = selectedDocumentId === null;
    const saveStateLabel = isSaving
        ? "Saving..."
        : hasUnsavedChanges
        ? "Unsaved changes"
        : isNewDocument
        ? "Draft"
        : null;
    const normalizedSearchTerm = searchTerm.trim().toLowerCase();
    const filteredDocuments = normalizedSearchTerm
        ? documents.filter((document) => (
            document.title.toLowerCase().includes(normalizedSearchTerm) ||
            document.category.toLowerCase().includes(normalizedSearchTerm) ||
            document.content_text.toLowerCase().includes(normalizedSearchTerm)
        ))
        : documents;

    const editor = useEditor({
        extensions: [
            StarterKit.configure({
                blockquote: false,
                codeBlock: false,
                horizontalRule: false,
            }),
        ],
        content: contentJson as Content,
        editable: isEditing,
        immediatelyRender: false,
        onUpdate: ({ editor }) => {
            if (isApplyingEditorContent.current) {
                return;
            }

            setContentJson(editor.getJSON() as DocumentContent);
            setHasUnsavedChanges(true);
            setSuccessMessage(null);
        },
    });

    useEffect(() => {
        async function loadDocuments() {
            try {
                setError(null);
                const data = await listDocuments();
                setDocuments(data);

                if (data.length > 0) {
                    const firstDocument = data[0];
                    setSelectedDocumentId(firstDocument.id);
                    setTitle(firstDocument.title);
                    setCategory(firstDocument.category);
                    setContentJson(firstDocument.content_json);
                    setIsEditing(false);
                    applyEditorContent(firstDocument.content_json);
                } else {
                    setIsEditing(true);
                    applyEditorContent(emptyDocumentContent);
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load documents.");
            } finally {
                setIsLoading(false);
            }
        }

        loadDocuments();
    }, []);

    useEffect(() => {
        if (!editor) {
            return;
        }

        editor.setOptions({ editable: isEditing });
    }, [editor, isEditing]);

    useEffect(() => {
        if (!editor) {
            return;
        }

        applyEditorContent(contentJson);
    }, [editor]);

    function applyEditorContent(nextContent: DocumentContent) {
        if (!editor) {
            return;
        }

        isApplyingEditorContent.current = true;
        editor.commands.setContent(nextContent as Content);
        isApplyingEditorContent.current = false;
    }

    function selectDocument(document: BusinessDocument) {
        setSelectedDocumentId(document.id);
        setTitle(document.title);
        setCategory(document.category);
        setContentJson(document.content_json);
        setIsEditing(false);
        setHasUnsavedChanges(false);
        applyEditorContent(document.content_json);
        setError(null);
        setSuccessMessage(null);
    }

    function startNewDocument() {
        setSelectedDocumentId(null);
        setTitle("");
        setCategory("General");
        setContentJson(emptyDocumentContent);
        setIsEditing(true);
        setHasUnsavedChanges(false);
        applyEditorContent(emptyDocumentContent);
        setError(null);
        setSuccessMessage(null);
    }

    function handleEdit() {
        setIsEditing(true);
        setSuccessMessage(null);
    }

    function handleCancelEdit() {
        if (selectedDocumentId === null) {
            startNewDocument();
            return;
        }

        const document = documents.find((currentDocument) => currentDocument.id === selectedDocumentId);
        if (document) {
            selectDocument(document);
        }
    }

    async function handleSave() {
        const trimmedTitle = title.trim();
        const trimmedCategory = category.trim() || "General";

        if (!trimmedTitle) {
            setError("Document title is required.");
            return;
        }

        try {
            setIsSaving(true);
            setError(null);
            setSuccessMessage(null);

            const savedDocument = isNewDocument
                ? await createDocument({
                    title: trimmedTitle,
                    category: trimmedCategory,
                    content_json: contentJson,
                })
                : await updateDocument(selectedDocumentId, {
                    title: trimmedTitle,
                    category: trimmedCategory,
                    content_json: contentJson,
                });

            setDocuments((currentDocuments) => {
                const remainingDocuments = currentDocuments.filter(
                    (document) => document.id !== savedDocument.id,
                );
                return [savedDocument, ...remainingDocuments];
            });
            setSelectedDocumentId(savedDocument.id);
            setTitle(savedDocument.title);
            setCategory(savedDocument.category);
            setContentJson(savedDocument.content_json);
            setIsEditing(false);
            setHasUnsavedChanges(false);
            applyEditorContent(savedDocument.content_json);
            setSuccessMessage("Document saved.");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to save document.");
        } finally {
            setIsSaving(false);
        }
    }

    async function handleDelete() {
        if (selectedDocumentId === null) {
            startNewDocument();
            return;
        }

        const confirmed = window.confirm("Delete this document?");
        if (!confirmed) {
            return;
        }

        try {
            setIsSaving(true);
            setError(null);
            setSuccessMessage(null);
            await deleteDocument(selectedDocumentId);

            const nextDocuments = documents.filter((document) => document.id !== selectedDocumentId);
            setDocuments(nextDocuments);

            if (nextDocuments.length > 0) {
                selectDocument(nextDocuments[0]);
            } else {
                startNewDocument();
            }
            setHasUnsavedChanges(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete document.");
        } finally {
            setIsSaving(false);
        }
    }

    return (
        <>
            <div className="page-header">
                <h2>Documents</h2>
                <p>Create business reference notes for policies, workflows, and service knowledge.</p>
            </div>

            {error && <p className="error-message">{error}</p>}
            {successMessage && <p className="success-message">{successMessage}</p>}

            <section className="documents-layout">
                <aside className="documents-sidebar" aria-label="Business documents">
                    <div className="documents-sidebar-header">
                        <h3>Documents</h3>
                        <button className="primary-button" type="button" onClick={startNewDocument}>
                            New
                        </button>
                    </div>

                    <label className="document-search">
                        <span>Search</span>
                        <input
                            type="search"
                            value={searchTerm}
                            onChange={(event) => setSearchTerm(event.target.value)}
                            placeholder="Search documents..."
                        />
                    </label>

                    {isLoading ? (
                        <p className="empty-state">Loading documents...</p>
                    ) : documents.length === 0 ? (
                        <div className="empty-state document-empty-state">
                            <strong>Create your first document</strong>
                            <span>Use documents for service steps, policies, and repeatable workflows.</span>
                        </div>
                    ) : filteredDocuments.length === 0 ? (
                        <p className="empty-state">No documents match your search.</p>
                    ) : (
                        <div className="document-list">
                            {filteredDocuments.map((document) => (
                                <button
                                    className={document.id === selectedDocumentId ? "document-list-item active" : "document-list-item"}
                                    key={document.id}
                                    type="button"
                                    onClick={() => selectDocument(document)}
                                >
                                    <span>{document.title}</span>
                                    <small>{document.category} · {formatUpdatedAt(document.updated_at)}</small>
                                    <p>{documentPreview(document)}</p>
                                </button>
                            ))}
                        </div>
                    )}
                </aside>

                <section className="document-editor-panel" aria-label="Document editor">
                    <div className="document-editor-header">
                        <div>
                            <span className="detail-label">{isNewDocument ? "New Document" : isEditing ? "Editing Document" : "Document"}</span>
                            <h3>{title.trim() || "Untitled document"}</h3>
                            {saveStateLabel && (
                                <p className={hasUnsavedChanges ? "document-save-state unsaved" : "document-save-state"}>
                                    {saveStateLabel}
                                </p>
                            )}
                        </div>
                        <div className="section-actions">
                            {isEditing ? (
                                <>
                                    <button className="action-button" type="button" onClick={handleCancelEdit} disabled={isSaving}>
                                        Cancel
                                    </button>
                                    <button className="primary-button" type="button" onClick={handleSave} disabled={isSaving}>
                                        {isSaving ? "Saving..." : "Save Document"}
                                    </button>
                                </>
                            ) : (
                                <>
                                    <button className="action-button" type="button" onClick={handleDelete} disabled={isSaving}>
                                        Delete
                                    </button>
                                    <button className="primary-button" type="button" onClick={handleEdit}>
                                        Edit
                                    </button>
                                </>
                            )}
                        </div>
                    </div>

                    {isEditing ? (
                        <div className="document-meta-grid">
                            <label className="form-field">
                                <span>Title</span>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(event) => {
                                        setTitle(event.target.value);
                                        setHasUnsavedChanges(true);
                                        setSuccessMessage(null);
                                    }}
                                />
                            </label>
                            <label className="form-field">
                                <span>Category</span>
                                <input
                                    type="text"
                                    value={category}
                                    onChange={(event) => {
                                        setCategory(event.target.value);
                                        setHasUnsavedChanges(true);
                                        setSuccessMessage(null);
                                    }}
                                />
                            </label>
                        </div>
                    ) : (
                        <div className="document-read-meta" aria-label="Document details">
                            <span>{category}</span>
                            <strong>{title.trim() || "Untitled document"}</strong>
                        </div>
                    )}

                    {isEditing && (
                        <div className="document-toolbar" aria-label="Document formatting">
                            <button
                                className={editor?.isActive("heading", { level: 2 }) ? "active" : ""}
                                type="button"
                                onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
                            >
                                Heading
                            </button>
                            <button
                                className={editor?.isActive("bold") ? "active" : ""}
                                type="button"
                                onClick={() => editor?.chain().focus().toggleBold().run()}
                            >
                                Bold
                            </button>
                            <button
                                className={editor?.isActive("italic") ? "active" : ""}
                                type="button"
                                onClick={() => editor?.chain().focus().toggleItalic().run()}
                            >
                                Italicize
                            </button>
                            <button
                                className={editor?.isActive("bulletList") ? "active" : ""}
                                type="button"
                                onClick={() => editor?.chain().focus().toggleBulletList().run()}
                            >
                                Bullets
                            </button>
                            <button
                                className={editor?.isActive("orderedList") ? "active" : ""}
                                type="button"
                                onClick={() => editor?.chain().focus().toggleOrderedList().run()}
                            >
                                Numbers
                            </button>
                        </div>
                    )}

                    <EditorContent className={isEditing ? "document-editor" : "document-editor document-editor-readonly"} editor={editor} />
                </section>
            </section>
        </>
    );
}
