import { useEffect, useMemo, useRef, useState, type SubmitEventHandler } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { getCustomer, listCustomerLocations, type Customer, type CustomerLocation } from "../api/customers";
import { createInvoiceItem, deleteInvoiceItem, updateInvoiceItem } from "../api/invoiceItems";
import { getInvoice, updateInvoice, updateInvoiceStatus, type Invoice, type InvoiceStatus } from "../api/invoices";
import { createPayment, listPayments, getPaymentSummary, PAYMENT_METHODS, type Payment, type PaymentMethod, type PaymentSummary } from "../api/payments";
import { createProduct, listProducts, type Product } from "../api/products";
import { addInvoiceTag, createTag, listInvoiceTags, listTags, removeInvoiceTag, type Tag } from "../api/tags";
import { formatDisplayDate, getDefaultSentInvoiceDueDate, getDefaultSentInvoiceIssuedDate } from "../utils/date";
import { centsToDollars, dollarsToCents } from "../utils/money";

function productLabel(product: Product | undefined, productId: number) {
    return product ? product.name : `Product #${productId}`;
}

function categoryLabel(product: Product | undefined) {
    return product?.category_name ?? "Uncategorized";
}

function formatLineItemDollars(cents: number) {
    const dollars = centsToDollars(cents);
    return dollars.endsWith(".00") ? dollars.slice(0, -3) : dollars;
}

function restoreScrollPosition(scrollY: number) {
    if (navigator.userAgent.includes("jsdom")) {
        return;
    }

    window.requestAnimationFrame(() => window.scrollTo({ top: scrollY }));
}

type InvoiceDetailLocationState = {
    fromCustomerId?: number;
};

type SelectedItemQuantities = Record<number, number>;

export function InvoiceDetailPage() {
    const { invoiceId } = useParams();
    const location = useLocation();
    const [invoice, setInvoice] = useState<Invoice | null>(null);
    const [customer, setCustomer] = useState<Customer | null>(null);
    const [customerLocations, setCustomerLocations] = useState<CustomerLocation[]>([]);
    const [payments, setPayments] = useState<Payment[]>([]);
    const [paymentSummary, setPaymentSummary] = useState<PaymentSummary | null>(null);
    const [products, setProducts] = useState<Product[]>([]);
    const [tags, setTags] = useState<Tag[]>([]);
    const [invoiceTags, setInvoiceTags] = useState<Tag[]>([]);
    const [isItemModalOpen, setIsItemModalOpen] = useState(false);
    const [itemSearch, setItemSearch] = useState("");
    const [selectedItemQuantities, setSelectedItemQuantities] = useState<SelectedItemQuantities>({});
    const [newItemName, setNewItemName] = useState("");
    const [newItemUnitCostDollars, setNewItemUnitCostDollars] = useState("");
    const [newItemUnitPriceDollars, setNewItemUnitPriceDollars] = useState("");
    const [isTagModalOpen, setIsTagModalOpen] = useState(false);
    const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);
    const [tagSearch, setTagSearch] = useState("");
    const [newTagName, setNewTagName] = useState("");
    const [isAddPaymentOpen, setIsAddPaymentOpen] = useState(false);
    const [paymentAmountDollars, setPaymentAmountDollars] = useState("");
    const [paymentDate, setPaymentDate] = useState("");
    const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("card");
    const [paymentNote, setPaymentNote] = useState("");
    const [isEditInvoiceLocationOpen, setIsEditInvoiceLocationOpen] = useState(false);
    const [editInvoiceLocationId, setEditInvoiceLocationId] = useState("");
    const [isEditInvoiceTitleOpen, setIsEditInvoiceTitleOpen] = useState(false);
    const [editInvoiceTitle, setEditInvoiceTitle] = useState("");
    const [isEditInvoiceDescriptionOpen, setIsEditInvoiceDescriptionOpen] = useState(false);
    const [editInvoiceDescription, setEditInvoiceDescription] = useState("");
    const [isSendDrawerOpen, setIsSendDrawerOpen] = useState(false);
    const [sendSubject, setSendSubject] = useState("");
    const [sendNote, setSendNote] = useState("");
    const [sendIssueDate, setSendIssueDate] = useState("");
    const [sendDueDate, setSendDueDate] = useState("");
    const [printIssueDateOverride, setPrintIssueDateOverride] = useState<string | null>(null);
    const [printDueDateOverride, setPrintDueDateOverride] = useState<string | null>(null);
    const [isItemSubmitting, setIsItemSubmitting] = useState(false);
    const [isTagSubmitting, setIsTagSubmitting] = useState(false);
    const [isPaymentSubmitting, setIsPaymentSubmitting] = useState(false);
    const [isInvoiceLocationSubmitting, setIsInvoiceLocationSubmitting] = useState(false);
    const [isInvoiceTitleSubmitting, setIsInvoiceTitleSubmitting] = useState(false);
    const [isInvoiceDescriptionSubmitting, setIsInvoiceDescriptionSubmitting] = useState(false);
    const [isSendingInvoice, setIsSendingInvoice] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);
    const sendDueDateInputRef = useRef<HTMLInputElement | null>(null);
    const locationState = location.state as InvoiceDetailLocationState | null;
    const backTarget = locationState?.fromCustomerId ? `/customers/${locationState.fromCustomerId}` : "/invoices";
    const backLabel = locationState?.fromCustomerId ? "Back to customer" : "Back to invoices";

    function handlePrintInvoice() {
        window.print();
    }

    function getNextStatuses(status: InvoiceStatus): InvoiceStatus[] {
        switch (status) {
            case "draft":
                return ["sent"];
            case "sent":
                return ["void"];
            case "paid":
            case "void":
                return [];
            default:
                return [];
        }
    }

    function getStatusActionLabel(status: InvoiceStatus) {
        switch (status) {
            case "sent":
                return "Send";
            case "void":
                return "Void";
            default:
                return status;
        }
    }

    function getInvoiceTitle(currentInvoice: Invoice) {
        return currentInvoice.title?.trim() || `Invoice #${currentInvoice.id}`;
    }

    function openSendDrawer() {
        if (!invoice) {
            return;
        }

        setActionError(null);
        setSendSubject(invoice.title?.trim() ? `${invoice.title.trim()} - Invoice #${invoice.id}` : `Invoice #${invoice.id}`);
        setSendNote("Thank you for your business. Please review the attached invoice when you have a moment.");
        setSendIssueDate(invoice.date_issued ?? getDefaultSentInvoiceIssuedDate());
        setSendDueDate(invoice.date_due ?? getDefaultSentInvoiceDueDate());
        setIsSendDrawerOpen(true);
    }

    function closeSendDrawer() {
        if (isSendingInvoice) {
            return;
        }

        setSendSubject("");
        setSendNote("");
        setSendIssueDate("");
        setSendDueDate("");
        setIsSendDrawerOpen(false);
    }

    function openSendDueDatePicker() {
        const input = sendDueDateInputRef.current as (HTMLInputElement & { showPicker?: () => void }) | null;
        input?.focus();
        input?.showPicker?.();
    }

    async function handlePreviewSendInvoice() {
        if (!invoice) {
            return;
        }

        setActionError(null);
        setPrintIssueDateOverride(sendIssueDate || invoice.date_issued);
        setPrintDueDateOverride(sendDueDate || invoice.date_due);
        window.requestAnimationFrame(() => {
            handlePrintInvoice();
            window.requestAnimationFrame(() => {
                setPrintIssueDateOverride(null);
                setPrintDueDateOverride(null);
            });
        });
    }

    async function loadInvoiceDetail() {
        const parsedInvoiceId = Number(invoiceId);

        if (!Number.isInteger(parsedInvoiceId) || parsedInvoiceId <= 0) {
            setError("Invalid invoice id.");
            setIsLoading(false);
            return;
        }

        try {
            setIsLoading(true);
            setError(null);

            const invoiceData = await getInvoice(parsedInvoiceId, true);
            const [customerData, locationData, paymentData, summaryData, productData, tagData, invoiceTagData] = await Promise.all([
                getCustomer(invoiceData.customer_id),
                listCustomerLocations(invoiceData.customer_id),
                listPayments(invoiceData.id),
                getPaymentSummary(invoiceData.id),
                listProducts(),
                listTags(true),
                listInvoiceTags(invoiceData.id),
            ]);

            setInvoice(invoiceData);
            setCustomer(customerData);
            setCustomerLocations(locationData);
            setPayments(paymentData);
            setPaymentSummary(summaryData);
            setProducts(productData);
            setTags(tagData);
            setInvoiceTags(invoiceTagData);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load invoice detail.");
        } finally {
            setIsLoading(false);
        }
    }

    async function refreshInvoiceSection(invoiceIdToRefresh: number) {
        const [invoiceData, summaryData] = await Promise.all([
            getInvoice(invoiceIdToRefresh, true),
            getPaymentSummary(invoiceIdToRefresh),
        ]);

        setInvoice(invoiceData);
        setPaymentSummary(summaryData);
    }

    async function refreshPaymentSection(invoiceIdToRefresh: number) {
        const [invoiceData, paymentData, summaryData] = await Promise.all([
            getInvoice(invoiceIdToRefresh, true),
            listPayments(invoiceIdToRefresh),
            getPaymentSummary(invoiceIdToRefresh),
        ]);

        setInvoice(invoiceData);
        setPayments(paymentData);
        setPaymentSummary(summaryData);
    }

    async function refreshInvoiceTags(invoiceIdToRefresh: number) {
        const invoiceTagData = await listInvoiceTags(invoiceIdToRefresh);
        setInvoiceTags(invoiceTagData);
    }

    useEffect(() => {
        loadInvoiceDetail();
    }, [invoiceId]);

    const productsById = useMemo(() => {
        return Object.fromEntries(products.map((product) => [product.id, product]));
    }, [products]);

    const activeProducts = useMemo(() => {
        return products.filter((product) => product.is_active);
    }, [products]);

    const filteredProducts = useMemo(() => {
        const normalizedSearch = itemSearch.trim().toLowerCase();

        if (!normalizedSearch) {
            return activeProducts;
        }

        return activeProducts.filter((product) => (
            product.name.toLowerCase().includes(normalizedSearch)
            || product.category_name?.toLowerCase().includes(normalizedSearch)
        ));
    }, [activeProducts, itemSearch]);

    const manageableTags = useMemo(() => {
        const tagMap = new Map(tags.map((tag) => [tag.id, tag]));
        invoiceTags.forEach((tag) => tagMap.set(tag.id, tag));
        return Array.from(tagMap.values()).sort((first, second) => first.name.localeCompare(second.name));
    }, [tags, invoiceTags]);

    const filteredTags = useMemo(() => {
        const normalizedSearch = tagSearch.trim().toLowerCase();

        if (!normalizedSearch) {
            return manageableTags;
        }

        return manageableTags.filter((tag) => tag.name.toLowerCase().includes(normalizedSearch));
    }, [manageableTags, tagSearch]);

    const invoiceLocation = useMemo(() => {
        if (!invoice?.location_id) {
            return null;
        }
        return customerLocations.find((location) => location.id === invoice.location_id) ?? null;
    }, [customerLocations, invoice]);

    function formatLocation(location: CustomerLocation) {
        const line2 = location.address_line2 ? `, ${location.address_line2}` : "";
        return `${location.address_line1}${line2}, ${location.city}, ${location.state} ${location.postal_code}`;
    }

    function openEditInvoiceLocation() {
        setActionError(null);
        setEditInvoiceLocationId(invoice?.location_id ? String(invoice.location_id) : "");
        setIsEditInvoiceLocationOpen(true);
    }

    function closeEditInvoiceLocation() {
        if (isInvoiceLocationSubmitting) {
            return;
        }

        setEditInvoiceLocationId("");
        setIsEditInvoiceLocationOpen(false);
    }

    function openEditInvoiceTitle() {
        setActionError(null);
        setEditInvoiceTitle(invoice?.title ?? "");
        setIsEditInvoiceTitleOpen(true);
    }

    function closeEditInvoiceTitle() {
        if (isInvoiceTitleSubmitting) {
            return;
        }

        setEditInvoiceTitle("");
        setIsEditInvoiceTitleOpen(false);
    }

    const handleUpdateInvoiceTitle: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!invoice) {
            return;
        }

        try {
            setIsInvoiceTitleSubmitting(true);
            setActionError(null);
            await updateInvoice(invoice.id, {
                title: editInvoiceTitle.trim() || null,
            });
            setEditInvoiceTitle("");
            setIsEditInvoiceTitleOpen(false);
            await refreshInvoiceSection(invoice.id);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to update invoice title.");
        } finally {
            setIsInvoiceTitleSubmitting(false);
        }
    };

    function openEditInvoiceDescription() {
        setActionError(null);
        setEditInvoiceDescription(invoice?.description ?? "");
        setIsEditInvoiceDescriptionOpen(true);
    }

    function closeEditInvoiceDescription() {
        if (isInvoiceDescriptionSubmitting) {
            return;
        }

        setEditInvoiceDescription("");
        setIsEditInvoiceDescriptionOpen(false);
    }

    const handleUpdateInvoiceDescription: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!invoice) {
            return;
        }

        try {
            setIsInvoiceDescriptionSubmitting(true);
            setActionError(null);
            await updateInvoice(invoice.id, {
                description: editInvoiceDescription.trim() || null,
            });
            setEditInvoiceDescription("");
            setIsEditInvoiceDescriptionOpen(false);
            await refreshInvoiceSection(invoice.id);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to update invoice description.");
        } finally {
            setIsInvoiceDescriptionSubmitting(false);
        }
    };

    const handleUpdateInvoiceLocation: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!invoice) {
            return;
        }

        try {
            setIsInvoiceLocationSubmitting(true);
            setActionError(null);
            await updateInvoice(invoice.id, {
                location_id: editInvoiceLocationId ? Number(editInvoiceLocationId) : null,
            });
            setEditInvoiceLocationId("");
            setIsEditInvoiceLocationOpen(false);
            await refreshInvoiceSection(invoice.id);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to update invoice location.");
        } finally {
            setIsInvoiceLocationSubmitting(false);
        }
    };

    async function handleStatusChange(nextStatus: InvoiceStatus) {
        if (!invoice) {
            return;
        }

        try {
            setActionError(null);
            await updateInvoiceStatus(invoice.id, nextStatus);
            await refreshInvoiceSection(invoice.id);
        } catch (err) {
            const message = err instanceof Error ? err.message : "Failed to update status.";
            setActionError(`Could not change invoice status. ${message}`);
        }
    }

    const handleSendInvoice: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!invoice) {
            return;
        }

        if (!sendIssueDate || !sendDueDate) {
            setActionError("Issued date and due date are required to send an invoice.");
            return;
        }

        try {
            setIsSendingInvoice(true);
            setActionError(null);
            if (sendIssueDate !== invoice.date_issued || sendDueDate !== invoice.date_due) {
                await updateInvoice(invoice.id, {
                    date_issued: sendIssueDate,
                    date_due: sendDueDate,
                });
            }

            await updateInvoiceStatus(invoice.id, "sent");
            setIsSendDrawerOpen(false);
            setSendSubject("");
            setSendNote("");
            setSendIssueDate("");
            setSendDueDate("");
            await refreshInvoiceSection(invoice.id);
        } catch (err) {
            const message = err instanceof Error ? err.message : "Failed to send invoice.";
            setActionError(`Could not send invoice. ${message}`);
        } finally {
            setIsSendingInvoice(false);
        }
    };

    function resetItemModal() {
        setItemSearch("");
        setSelectedItemQuantities({});
        setNewItemName("");
        setNewItemUnitCostDollars("");
        setNewItemUnitPriceDollars("");
    }

    function openItemModal() {
        setActionError(null);
        resetItemModal();
        setIsItemModalOpen(true);
    }

    function closeItemModal() {
        if (isItemSubmitting) {
            return;
        }

        resetItemModal();
        setIsItemModalOpen(false);
    }

    function toggleSelectedItem(productId: number) {
        setSelectedItemQuantities((currentQuantities) => {
            if (currentQuantities[productId]) {
                const { [productId]: _removedQuantity, ...nextQuantities } = currentQuantities;
                return nextQuantities;
            }

            return {
                ...currentQuantities,
                [productId]: 1,
            };
        });
    }

    function updateSelectedItemQuantity(productId: number, quantity: number) {
        if (quantity < 1) {
            return;
        }

        setSelectedItemQuantities((currentQuantities) => ({
            ...currentQuantities,
            [productId]: quantity,
        }));
    }

    async function handleCreateItemFromModal() {
        if (!newItemName.trim()) {
            setActionError("Item name is required.");
            return;
        }

        let unitCostCents = 0;
        if (newItemUnitCostDollars.trim()) {
            try {
                unitCostCents = dollarsToCents(newItemUnitCostDollars);
            } catch (err) {
                setActionError(err instanceof Error ? err.message : "Enter a valid unit cost.");
                return;
            }
        }

        if (!newItemUnitPriceDollars.trim()) {
            setActionError("Unit price is required.");
            return;
        }

        let unitPriceCents: number;
        try {
            unitPriceCents = dollarsToCents(newItemUnitPriceDollars);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Enter a valid unit price.");
            return;
        }

        try {
            setIsItemSubmitting(true);
            setActionError(null);
            const product = await createProduct({
                name: newItemName.trim(),
                cost_cents: unitCostCents,
                unit_price_cents: unitPriceCents,
                is_active: true,
            });
            setProducts((currentProducts) => [...currentProducts, product]);
            setSelectedItemQuantities((currentQuantities) => ({
                ...currentQuantities,
                [product.id]: currentQuantities[product.id] ?? 1,
            }));
            setNewItemName("");
            setNewItemUnitCostDollars("");
            setNewItemUnitPriceDollars("");
            setItemSearch("");
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to create item.");
        } finally {
            setIsItemSubmitting(false);
        }
    }

    async function handleSaveInvoiceItems() {
        if (!invoice) {
            return;
        }

        const selectedEntries = Object.entries(selectedItemQuantities)
            .map(([productId, quantity]) => [Number(productId), quantity] as const)
            .filter(([, quantity]) => quantity > 0);

        if (selectedEntries.length === 0) {
            setActionError("Select at least one item.");
            return;
        }

        try {
            setIsItemSubmitting(true);
            setActionError(null);
            const scrollY = window.scrollY;

            for (const [productId, quantity] of selectedEntries) {
                const selectedProduct = productsById[productId];
                if (!selectedProduct) {
                    continue;
                }

                const matchingItem = invoice.items?.find((item) => (
                    item.product_id === productId
                    && item.unit_cost_cents === selectedProduct.cost_cents
                    && item.unit_price_cents === selectedProduct.unit_price_cents
                ));

                if (matchingItem) {
                    await updateInvoiceItem(matchingItem.id, {
                        quantity: matchingItem.quantity + quantity,
                    });
                } else {
                    await createInvoiceItem(invoice.id, {
                        product_id: productId,
                        quantity,
                        unit_cost_cents: null,
                        unit_price_cents: null,
                    });
                }
            }

            resetItemModal();
            setIsItemModalOpen(false);
            await refreshInvoiceSection(invoice.id);
            restoreScrollPosition(scrollY);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to update line items.");
        } finally {
            setIsItemSubmitting(false);
        }
    }

    async function handleDeleteInvoiceItem(itemId: number) {
        try {
            setActionError(null);
            const scrollY = window.scrollY;
            await deleteInvoiceItem(itemId);
            if (invoice) {
                await refreshInvoiceSection(invoice.id);
            }
            restoreScrollPosition(scrollY);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to delete line item.");
        }
    }

    async function handleChangeInvoiceItemQuantity(itemId: number, quantity: number) {
        if (quantity < 1) {
            return;
        }

        try {
            setActionError(null);
            const scrollY = window.scrollY;
            await updateInvoiceItem(itemId, { quantity });
            if (invoice) {
                await refreshInvoiceSection(invoice.id);
            }
            restoreScrollPosition(scrollY);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to update line item quantity.");
        }
    }

    function resetTagModal() {
        setSelectedTagIds([]);
        setTagSearch("");
        setNewTagName("");
    }

    function openTagModal() {
        setActionError(null);
        setSelectedTagIds(invoiceTags.map((tag) => tag.id));
        setTagSearch("");
        setNewTagName("");
        setIsTagModalOpen(true);
    }

    function closeTagModal() {
        if (isTagSubmitting) {
            return;
        }

        resetTagModal();
        setIsTagModalOpen(false);
    }

    function toggleSelectedTag(tagId: number) {
        setSelectedTagIds((currentTagIds) => (
            currentTagIds.includes(tagId)
                ? currentTagIds.filter((currentTagId) => currentTagId !== tagId)
                : [...currentTagIds, tagId]
        ));
    }

    async function handleCreateTagFromModal() {
        if (!newTagName.trim()) {
            setActionError("Tag name is required.");
            return;
        }

        try {
            setIsTagSubmitting(true);
            setActionError(null);
            const tag = await createTag({
                name: newTagName.trim(),
                is_active: true,
            });
            setTags((currentTags) => [...currentTags, tag]);
            setSelectedTagIds((currentTagIds) => (
                currentTagIds.includes(tag.id) ? currentTagIds : [...currentTagIds, tag.id]
            ));
            setNewTagName("");
            setTagSearch("");
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to create tag.");
        } finally {
            setIsTagSubmitting(false);
        }
    }

    async function handleSaveInvoiceTags() {
        if (!invoice) {
            return;
        }

        try {
            setIsTagSubmitting(true);
            setActionError(null);

            const currentTagIds = new Set(invoiceTags.map((tag) => tag.id));
            const nextTagIds = new Set(selectedTagIds);
            const tagIdsToAdd = selectedTagIds.filter((tagId) => !currentTagIds.has(tagId));
            const tagIdsToRemove = invoiceTags
                .map((tag) => tag.id)
                .filter((tagId) => !nextTagIds.has(tagId));

            await Promise.all([
                ...tagIdsToAdd.map((tagId) => addInvoiceTag(invoice.id, { tag_id: tagId })),
                ...tagIdsToRemove.map((tagId) => removeInvoiceTag(invoice.id, tagId)),
            ]);

            resetTagModal();
            setIsTagModalOpen(false);
            await refreshInvoiceTags(invoice.id);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to update tags.");
        } finally {
            setIsTagSubmitting(false);
        }
    }

    async function handleRemoveInvoiceTag(tagId: number) {
        if (!invoice) {
            return;
        }

        try {
            setActionError(null);
            await removeInvoiceTag(invoice.id, tagId);
            await refreshInvoiceTags(invoice.id);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to remove tag.");
        }
    }

    function resetPaymentForm() {
        setPaymentAmountDollars("");
        setPaymentDate("");
        setPaymentMethod("card");
        setPaymentNote("");
    }

    function openAddPayment() {
        setActionError(null);
        setIsAddPaymentOpen(true);
    }

    function closeAddPayment() {
        if (isPaymentSubmitting) {
            return;
        }

        resetPaymentForm();
        setIsAddPaymentOpen(false);
    }

    const handleAddPayment: SubmitEventHandler<HTMLFormElement> = async (event) => {
        event.preventDefault();

        if (!invoice) {
            return;
        }

        if (!paymentAmountDollars.trim()) {
            setActionError("Payment amount is required.");
            return;
        }

        if (!paymentDate) {
            setActionError("Payment date is required.");
            return;
        }

        let amountCents: number;
        try {
            amountCents = dollarsToCents(paymentAmountDollars);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Enter a valid payment amount.");
            return;
        }

        try {
            setIsPaymentSubmitting(true);
            setActionError(null);
            await createPayment(invoice.id, {
                amount_cents: amountCents,
                payment_date: paymentDate,
                method: paymentMethod,
                note: paymentNote.trim() || null,
            });
            resetPaymentForm();
            setIsAddPaymentOpen(false);
            await refreshPaymentSection(invoice.id);
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to add payment.");
        } finally {
            setIsPaymentSubmitting(false);
        }
    };

    return (
        <>
            <div className="page-header">
                <div className="detail-header-actions print-hidden">
                    <Link className="back-link" to={backTarget}>
                        {backLabel}
                    </Link>
                    <div className="detail-header-action-group">
                        <button className="action-button" type="button" onClick={handlePrintInvoice}>
                            Print
                        </button>
                        {invoice && getNextStatuses(invoice.status).map((nextStatus) => (
                            <button
                                className="action-button"
                                key={nextStatus}
                                type="button"
                                onClick={() => nextStatus === "sent" ? openSendDrawer() : handleStatusChange(nextStatus)}
                            >
                                {getStatusActionLabel(nextStatus)}
                            </button>
                        ))}
                    </div>
                </div>
                <h2>{invoice ? getInvoiceTitle(invoice) : "Invoice Detail"}</h2>
                <p>Review invoice customer, line items, and payment history.</p>
            </div>

            {isLoading ? (
                <p>Loading invoice...</p>
            ) : error ? (
                <p className="error-message">{error}</p>
            ) : invoice ? (
                <>
                    {(() => {
                        const printableIssueDate = printIssueDateOverride ?? invoice.date_issued;
                        const printableDueDate = printDueDateOverride ?? invoice.date_due;

                        return (
                    <section className="invoice-print-document print-only" aria-label="Printable customer invoice">
                        <header className="invoice-print-header">
                            <div>
                                <p className="invoice-print-brand">InvoiceDB</p>
                                <h1>{getInvoiceTitle(invoice)}</h1>
                            </div>
                            <dl>
                                <div>
                                    <dt>Issued</dt>
                                    <dd>{formatDisplayDate(printableIssueDate)}</dd>
                                </div>
                                <div>
                                    <dt>Due</dt>
                                    <dd>{formatDisplayDate(printableDueDate)}</dd>
                                </div>
                            </dl>
                        </header>

                        <section className="invoice-print-bill-to">
                            <span>Bill To</span>
                            <strong>{customer ? customer.name : `Customer #${invoice.customer_id}`}</strong>
                            {customer?.email && <p>{customer.email}</p>}
                            {invoiceLocation && <p>{formatLocation(invoiceLocation)}</p>}
                        </section>

                        <section className="invoice-print-section">
                            <h2>Line Items</h2>
                            {!invoice.items || invoice.items.length === 0 ? (
                                <p>No line items found for this invoice.</p>
                            ) : (
                                <table className="invoice-print-table">
                                    <thead>
	                                        <tr>
	                                            <th>Product</th>
	                                            <th>Unit Price</th>
	                                            <th>Quantity</th>
	                                            <th>Total Price</th>
	                                        </tr>
                                    </thead>
                                    <tbody>
	                                        {invoice.items.map((item) => (
	                                            <tr key={item.id}>
	                                                <td>{productLabel(productsById[item.product_id], item.product_id)}</td>
	                                                <td>${formatLineItemDollars(item.unit_price_cents)}</td>
	                                                <td>{item.quantity}</td>
	                                                <td>${formatLineItemDollars(item.line_total_cents)}</td>
	                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </section>

                        {invoice.description && (
                            <section className="invoice-print-section">
                                <h2>Work Description</h2>
                                <p className="invoice-description-text">{invoice.description}</p>
                            </section>
                        )}

                        <section className="invoice-print-totals" aria-label="Printable invoice totals">
                            <dl>
                                <div>
                                    <dt>Total</dt>
                                    <dd>${centsToDollars(invoice.total)}</dd>
                                </div>
                                <div>
                                    <dt>Amount Paid</dt>
                                    <dd>${centsToDollars(paymentSummary?.amount_paid_cents ?? 0)}</dd>
                                </div>
                                <div className="invoice-print-balance">
                                    <dt>Balance Due</dt>
                                    <dd>${centsToDollars(paymentSummary?.balance_due_cents ?? invoice.total)}</dd>
                                </div>
                            </dl>
                        </section>
                    </section>
                        );
                    })()}

                    <section className="detail-stack screen-only">
                    <section className="detail-panel">
                        <div>
                            <span className="detail-label">Title</span>
                            <h3>{getInvoiceTitle(invoice)}</h3>
                            <button className="tiny-action-button" type="button" onClick={openEditInvoiceTitle}>
                                Edit
                            </button>
                        </div>
                        <dl className="detail-grid">
                            <div>
                                <dt>Invoice #</dt>
                                <dd>#{invoice.id}</dd>
                            </div>
                            <div>
                                <dt>Customer</dt>
                                <dd>
                                    <Link className="detail-inline-link" to={`/customers/${invoice.customer_id}`} state={{ fromInvoiceId: invoice.id }}>
                                        {customer ? customer.name : `Customer #${invoice.customer_id}`}
                                    </Link>
                                </dd>
                            </div>
                            <div>
                                <dt>Status</dt>
                                <dd><span className="status-badge">{invoice.status}</span></dd>
                            </div>
                            <div>
                                <dt>Location</dt>
                                <dd className="inline-detail-value">
                                    {invoiceLocation ? (
                                        <Link
                                            className="detail-inline-link"
                                            to={`/locations/${invoiceLocation.location_id}`}
                                            state={{ fromInvoiceId: invoice.id }}
                                        >
                                            {invoiceLocation.label} - {formatLocation(invoiceLocation)}
                                        </Link>
                                    ) : (
                                        <span>-</span>
                                    )}
                                    <button
                                        className="tiny-action-button"
                                        type="button"
                                        onClick={openEditInvoiceLocation}
                                        aria-label="Edit invoice location"
                                    >
                                        Edit
                                    </button>
                                </dd>
                            </div>
                            <div>
                                <dt>Total</dt>
                                <dd>${centsToDollars(invoice.total)}</dd>
                            </div>
                            <div>
                                <dt>Issued</dt>
                                <dd>{formatDisplayDate(invoice.date_issued)}</dd>
                            </div>
                            <div>
                                <dt>Due</dt>
                                <dd>{formatDisplayDate(invoice.date_due)}</dd>
                            </div>
                        </dl>
                    </section>

                    <section className="detail-summary-grid" aria-label="Invoice payment summary">
                        <div>
                            <span>Balance Due</span>
                            <strong>${centsToDollars(paymentSummary?.balance_due_cents ?? invoice.total)}</strong>
                        </div>
                        <div>
                            <span>Paid</span>
                            <strong>${centsToDollars(paymentSummary?.amount_paid_cents ?? 0)}</strong>
                        </div>
                        <div>
                            <span>Cost</span>
                            <strong>${centsToDollars(invoice.cost_total_cents ?? 0)}</strong>
                        </div>
                        <div>
                            <span>Profit</span>
                            <strong>${centsToDollars(invoice.profit_total_cents ?? 0)}</strong>
                        </div>
                    </section>

                    {actionError && <p className="error-message">{actionError}</p>}

                    <section className="detail-panel invoice-description-panel">
                        <div className="section-header">
                            <h3>Line Items</h3>
                            <div className="section-actions stacked-section-actions">
                                <span className="section-count inline-section-count">{invoice.items?.length ?? 0} items</span>
                                {invoice.status === "draft" && (
                                    <button className="primary-button" type="button" onClick={openItemModal}>
                                        Add Items
                                    </button>
                                )}
                            </div>
                        </div>

                        {!invoice.items || invoice.items.length === 0 ? (
                            <p className="empty-state">No line items found for this invoice.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
	                                            <th>Product</th>
	                                            <th>Category</th>
	                                            <th>Unit Cost</th>
	                                            <th>Total Cost</th>
	                                            <th>Quantity</th>
	                                            <th>Unit Price</th>
	                                            <th>Total Price</th>
                                            <th>Profit</th>
                                            {invoice.status === "draft" && <th>Actions</th>}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {invoice.items.map((item) => (
	                                            <tr key={item.id}>
	                                                <td>{productLabel(productsById[item.product_id], item.product_id)}</td>
	                                                <td>{categoryLabel(productsById[item.product_id])}</td>
	                                                <td>${formatLineItemDollars(item.unit_cost_cents)}</td>
	                                                <td>${formatLineItemDollars(item.cost_total_cents)}</td>
	                                                <td>
	                                                    {invoice.status === "draft" ? (
	                                                        <div className="quantity-stepper">
                                                            <button
                                                                type="button"
                                                                aria-label={`Decrease quantity for ${productLabel(productsById[item.product_id], item.product_id)}`}
                                                                onClick={() => handleChangeInvoiceItemQuantity(item.id, item.quantity - 1)}
                                                                disabled={item.quantity <= 1}
                                                            >
                                                                -
                                                            </button>
                                                            <span>{item.quantity}</span>
                                                            <button
                                                                type="button"
                                                                aria-label={`Increase quantity for ${productLabel(productsById[item.product_id], item.product_id)}`}
                                                                onClick={() => handleChangeInvoiceItemQuantity(item.id, item.quantity + 1)}
                                                            >
                                                                +
                                                            </button>
                                                        </div>
                                                    ) : (
	                                                        item.quantity
	                                                    )}
	                                                </td>
	                                                <td>${formatLineItemDollars(item.unit_price_cents)}</td>
                                                <td>${formatLineItemDollars(item.line_total_cents)}</td>
                                                <td>${formatLineItemDollars(item.profit_total_cents)}</td>
                                                {invoice.status === "draft" && (
                                                    <td>
                                                        <button
                                                            className="small-action-button"
                                                            type="button"
                                                            onClick={() => handleDeleteInvoiceItem(item.id)}
                                                        >
                                                            Delete
                                                        </button>
                                                    </td>
                                                )}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>

                    <section className="detail-panel invoice-description-panel">
                        <div className="section-header">
                            <h3>Work Description</h3>
                            <div className="section-actions">
                                <button className="primary-button" type="button" onClick={openEditInvoiceDescription}>
                                    Edit Description
                                </button>
                            </div>
                        </div>

                        {invoice.description ? (
                            <p className="invoice-description-text">{invoice.description}</p>
                        ) : (
                            <p className="empty-state">No work description added for this invoice.</p>
                        )}
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Tags</h3>
                            <div className="section-actions">
                                <button className="primary-button" type="button" onClick={openTagModal}>
                                    Manage Tags
                                </button>
                            </div>
                        </div>

                        {invoiceTags.length === 0 ? (
                            <p className="empty-state">No tags assigned to this invoice.</p>
                        ) : (
                            <div className="tag-list" aria-label="Invoice tags">
                                {invoiceTags.map((tag) => (
                                    <span className="tag-chip" key={tag.id}>
                                        <Link
                                            aria-label={`View ${tag.name} tag`}
                                            to={`/tags/${tag.id}`}
                                            state={{ fromInvoiceId: invoice.id }}
                                        >
                                            {tag.name}
                                        </Link>
                                        <button
                                            type="button"
                                            aria-label={`Remove ${tag.name} tag`}
                                            onClick={() => handleRemoveInvoiceTag(tag.id)}
                                        >
                                            x
                                        </button>
                                    </span>
                                ))}
                            </div>
                        )}
                    </section>

                    <section className="detail-panel">
                        <div className="section-header">
                            <h3>Payments</h3>
                            <div className="section-actions">
                                <button className="primary-button" type="button" onClick={openAddPayment}>
                                    Add Payment
                                </button>
                            </div>
                        </div>

                        {payments.length === 0 ? (
                            <p className="empty-state">No payments found for this invoice.</p>
                        ) : (
                            <div className="table-wrapper detail-table-wrapper">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Method</th>
                                            <th>Amount</th>
                                            <th>Note</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {payments.map((payment) => (
                                            <tr key={payment.id}>
                                                <td>{formatDisplayDate(payment.payment_date)}</td>
                                                <td>{payment.method}</td>
                                                <td>${centsToDollars(payment.amount_cents)}</td>
                                                <td>{payment.note || "-"}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </section>
                    </section>

                    {isSendDrawerOpen && (
                        <div className="drawer-overlay" role="presentation" onMouseDown={closeSendDrawer}>
                            <form
                                className="send-invoice-drawer"
                                role="dialog"
                                aria-modal="true"
                                aria-labelledby="send-invoice-title"
                                onSubmit={handleSendInvoice}
                                onMouseDown={(event) => event.stopPropagation()}
                            >
                                <div className="send-drawer-header">
                                    <h3 id="send-invoice-title">Send Invoice</h3>
                                    <button className="icon-button" type="button" aria-label="Close send invoice" onClick={closeSendDrawer}>
                                        x
                                    </button>
                                </div>

                                <div className="send-drawer-body">
                                    <section className="send-review-card" aria-label="Invoice send summary">
                                        <div>
                                            <span>Customer</span>
                                            <strong>{customer?.name ?? `Customer #${invoice.customer_id}`}</strong>
                                        </div>
                                        <div>
                                            <span>Email</span>
                                            <strong>{customer?.email ?? "-"}</strong>
                                        </div>
                                        <div>
                                            <span>Invoice</span>
                                            <strong>#{invoice.id}</strong>
                                        </div>
                                        <div>
                                            <span>Due</span>
                                            <div className="send-due-date-control">
                                                <strong>{formatDisplayDate(sendDueDate)}</strong>
                                                <button
                                                    className="send-due-date-button"
                                                    type="button"
                                                    aria-label="Open due date calendar"
                                                    onClick={openSendDueDatePicker}
                                                >
                                                    <svg aria-hidden="true" viewBox="0 0 24 24" focusable="false">
                                                        <path d="M7 2v3M17 2v3M4 9h16M6 5h12a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" />
                                                    </svg>
                                                </button>
                                                <input
                                                    ref={sendDueDateInputRef}
                                                    className="send-due-date-input"
                                                    aria-label="Change due date"
                                                    type="date"
                                                    value={sendDueDate}
                                                    onChange={(event) => setSendDueDate(event.target.value)}
                                                    required
                                                    tabIndex={-1}
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <span>Issued</span>
                                            <strong>{formatDisplayDate(sendIssueDate)}</strong>
                                        </div>
                                        <div>
                                            <span>Balance</span>
                                            <strong>${centsToDollars(paymentSummary?.balance_due_cents ?? invoice.total)}</strong>
                                        </div>
                                    </section>

                                    <div className="form-field send-form-field">
                                        <label htmlFor="send-invoice-subject">Subject</label>
                                        <input
                                            id="send-invoice-subject"
                                            type="text"
                                            value={sendSubject}
                                            onChange={(event) => setSendSubject(event.target.value)}
                                        />
                                    </div>

                                    <div className="form-field send-form-field">
                                        <label htmlFor="send-invoice-note">Note</label>
                                        <textarea
                                            id="send-invoice-note"
                                            value={sendNote}
                                            onChange={(event) => setSendNote(event.target.value)}
                                            rows={5}
                                        />
                                    </div>
                                </div>

                                <div className="send-drawer-actions">
                                    <button className="secondary-button" type="button" onClick={closeSendDrawer} disabled={isSendingInvoice}>
                                        Cancel
                                    </button>
                                    <button className="secondary-button" type="button" onClick={handlePreviewSendInvoice} disabled={isSendingInvoice}>
                                        Preview Invoice
                                    </button>
                                    <button className="primary-button" type="submit" disabled={isSendingInvoice}>
                                        {isSendingInvoice ? "Sending..." : "Send Invoice"}
                                    </button>
                                </div>
                            </form>
                        </div>
                    )}

                    {isEditInvoiceTitleOpen && (
                        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="edit-invoice-title-heading">
                            <form className="modal-panel detail-panel" onSubmit={handleUpdateInvoiceTitle}>
                                <div className="modal-header">
                                    <h3 id="edit-invoice-title-heading">Edit Title</h3>
                                    <button className="icon-button" type="button" onClick={closeEditInvoiceTitle} aria-label="Close edit title">
                                        x
                                    </button>
                                </div>
                                <div className="form-grid modal-form-grid">
                                    <div className="form-field">
                                        <label htmlFor="edit-invoice-title">Title</label>
                                        <input
                                            id="edit-invoice-title"
                                            type="text"
                                            value={editInvoiceTitle}
                                            onChange={(event) => setEditInvoiceTitle(event.target.value)}
                                            placeholder={`Invoice #${invoice.id}`}
                                        />
                                    </div>
                                    <div className="modal-actions">
                                        <button className="secondary-button" type="button" onClick={closeEditInvoiceTitle} disabled={isInvoiceTitleSubmitting}>
                                            Cancel
                                        </button>
                                        <button className="primary-button" type="submit" disabled={isInvoiceTitleSubmitting}>
                                            {isInvoiceTitleSubmitting ? "Saving..." : "Save Title"}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    )}

                    {isEditInvoiceDescriptionOpen && (
                        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="edit-invoice-description-heading">
                            <form className="modal-panel detail-panel" onSubmit={handleUpdateInvoiceDescription}>
                                <div className="modal-header">
                                    <h3 id="edit-invoice-description-heading">Edit Description</h3>
                                    <button className="icon-button" type="button" onClick={closeEditInvoiceDescription} aria-label="Close edit description">
                                        x
                                    </button>
                                </div>
                                <div className="form-grid modal-form-grid">
                                    <div className="form-field">
                                        <label htmlFor="edit-invoice-description">Description</label>
                                        <textarea
                                            id="edit-invoice-description"
                                            value={editInvoiceDescription}
                                            onChange={(event) => setEditInvoiceDescription(event.target.value)}
                                            rows={5}
                                            placeholder="Describe the work performed"
                                        />
                                    </div>
                                    <div className="modal-actions">
                                        <button className="secondary-button" type="button" onClick={closeEditInvoiceDescription} disabled={isInvoiceDescriptionSubmitting}>
                                            Cancel
                                        </button>
                                        <button className="primary-button" type="submit" disabled={isInvoiceDescriptionSubmitting}>
                                            {isInvoiceDescriptionSubmitting ? "Saving..." : "Save Description"}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    )}

                    {isEditInvoiceLocationOpen && (
                        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="edit-invoice-location-title">
                            <form className="modal-panel detail-panel" onSubmit={handleUpdateInvoiceLocation}>
                                <div className="modal-header">
                                    <h3 id="edit-invoice-location-title">Edit Location</h3>
                                    <button className="icon-button" type="button" onClick={closeEditInvoiceLocation} aria-label="Close edit location">
                                        x
                                    </button>
                                </div>
                                <div className="form-grid modal-form-grid">
                                    <div className="form-field">
                                        <label htmlFor="invoice-detail-location">Location</label>
                                        <select
                                            id="invoice-detail-location"
                                            value={editInvoiceLocationId}
                                            onChange={(event) => setEditInvoiceLocationId(event.target.value)}
                                        >
                                            <option value="">No location</option>
                                            {customerLocations.map((location) => (
                                                <option key={location.id} value={location.id}>
                                                    {location.label} - {formatLocation(location)}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="modal-actions">
                                        <button className="secondary-button" type="button" onClick={closeEditInvoiceLocation} disabled={isInvoiceLocationSubmitting}>
                                            Cancel
                                        </button>
                                        <button className="primary-button" type="submit" disabled={isInvoiceLocationSubmitting}>
                                            {isInvoiceLocationSubmitting ? "Saving..." : "Save Location"}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    )}

                    {isItemModalOpen && (
                        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="add-items-title">
                            <form className="modal-panel detail-panel invoice-modal-panel" onSubmit={(event) => {
                                event.preventDefault();
                                handleSaveInvoiceItems();
                            }}>
                                <div className="modal-header">
                                    <h3 id="add-items-title">Add Items</h3>
                                    <button className="icon-button" type="button" onClick={closeItemModal} aria-label="Close add items">
                                        x
                                    </button>
                                </div>
                                <div className="form-grid modal-form-grid">
                                    <div className="form-field">
                                        <label htmlFor="item-search">Search Items</label>
                                        <input
                                            id="item-search"
                                            value={itemSearch}
                                            onChange={(event) => setItemSearch(event.target.value)}
                                            placeholder="Search products"
                                        />
                                    </div>
                                    <div className="item-picker-list" aria-label="Available items">
                                        {filteredProducts.length === 0 ? (
                                            <p className="empty-state">No items match your search.</p>
                                        ) : (
                                            filteredProducts.map((product) => {
                                                const selectedQuantity = selectedItemQuantities[product.id] ?? 0;
                                                const isSelected = selectedQuantity > 0;

                                                return (
                                                    <div className="item-picker-row" key={product.id}>
                                                        <label className="item-picker-check">
                                                            <input
                                                                type="checkbox"
                                                                checked={isSelected}
                                                                onChange={() => toggleSelectedItem(product.id)}
                                                            />
                                                            <span className="picker-row-content">
                                                                <strong>{product.name}</strong>
                                                                <span className="item-picker-meta">
                                                                    {product.category_name ?? "Uncategorized"} - ${centsToDollars(product.unit_price_cents)}
                                                                </span>
                                                            </span>
                                                        </label>
                                                        <input
                                                            aria-label={`Quantity for ${product.name}`}
                                                            className="quantity-input"
                                                            type="number"
                                                            min="1"
                                                            value={isSelected ? selectedQuantity : 1}
                                                            disabled={!isSelected}
                                                            onChange={(event) => updateSelectedItemQuantity(product.id, Number(event.target.value))}
                                                        />
                                                    </div>
                                                );
                                            })
                                        )}
                                    </div>
                                    <div className="form-section-heading">
                                        <h4>Create Item</h4>
                                    </div>
                                    <div className="inline-create-row item-create-row">
                                        <input
                                            aria-label="Name for new invoice detail item"
                                            type="text"
                                            value={newItemName}
                                            onChange={(event) => setNewItemName(event.target.value)}
                                            placeholder="Item name"
                                        />
                                        <input
                                            aria-label="Cost for new invoice detail item"
                                            type="text"
                                            value={newItemUnitCostDollars}
                                            onChange={(event) => setNewItemUnitCostDollars(event.target.value)}
                                            placeholder="Cost"
                                        />
                                        <input
                                            aria-label="Price for new invoice detail item"
                                            type="text"
                                            value={newItemUnitPriceDollars}
                                            onChange={(event) => setNewItemUnitPriceDollars(event.target.value)}
                                            placeholder="Price"
                                        />
                                        <button
                                            className="small-action-button"
                                            type="button"
                                            onClick={handleCreateItemFromModal}
                                            disabled={isItemSubmitting}
                                        >
                                            Add New Item
                                        </button>
                                    </div>
                                    <div className="modal-actions">
                                        <button className="secondary-button" type="button" onClick={closeItemModal} disabled={isItemSubmitting}>
                                            Cancel
                                        </button>
                                        <button className="primary-button" type="submit" disabled={isItemSubmitting}>
                                            {isItemSubmitting ? "Saving..." : "Save Items"}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    )}

                    {isTagModalOpen && (
                        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="manage-tags-title">
                            <form className="modal-panel detail-panel" onSubmit={(event) => {
                                event.preventDefault();
                                handleSaveInvoiceTags();
                            }}>
                                <div className="modal-header">
                                    <h3 id="manage-tags-title">Manage Tags</h3>
                                    <button className="icon-button" type="button" onClick={closeTagModal} aria-label="Close manage tags">
                                        x
                                    </button>
                                </div>
                                <div className="form-grid modal-form-grid">
                                    <div className="form-field">
                                        <label htmlFor="tag-search">Search Tags</label>
                                        <input
                                            id="tag-search"
                                            value={tagSearch}
                                            onChange={(event) => setTagSearch(event.target.value)}
                                            placeholder="Search by tag name"
                                        />
                                    </div>
                                    <div className="tag-picker-list" aria-label="Available tags">
                                        {filteredTags.length === 0 ? (
                                            <p className="empty-state">No tags match your search.</p>
                                        ) : (
                                            filteredTags.map((tag) => (
                                                <label className="tag-picker-row" key={tag.id}>
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedTagIds.includes(tag.id)}
                                                        onChange={() => toggleSelectedTag(tag.id)}
                                                    />
                                                    <span>{tag.name}</span>
                                                </label>
                                            ))
                                        )}
                                    </div>
                                    <div className="form-section-heading">
                                        <h4>Create Tag</h4>
                                    </div>
                                    <div className="inline-create-row">
                                        <input
                                            aria-label="Name for new invoice tag"
                                            value={newTagName}
                                            onChange={(event) => setNewTagName(event.target.value)}
                                            placeholder="Tag name"
                                        />
                                        <button
                                            className="small-action-button"
                                            type="button"
                                            onClick={handleCreateTagFromModal}
                                            disabled={isTagSubmitting}
                                        >
                                            Add New Tag
                                        </button>
                                    </div>
                                    <div className="modal-actions">
                                        <button className="secondary-button" type="button" onClick={closeTagModal} disabled={isTagSubmitting}>
                                            Cancel
                                        </button>
                                        <button className="primary-button" type="submit" disabled={isTagSubmitting}>
                                            {isTagSubmitting ? "Saving..." : "Save Tags"}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    )}

                    {isAddPaymentOpen && (
                        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="add-payment-title">
                            <form className="modal-panel detail-panel" onSubmit={handleAddPayment}>
                                <div className="modal-header">
                                    <h3 id="add-payment-title">Add Payment</h3>
                                    <button className="icon-button" type="button" onClick={closeAddPayment} aria-label="Close add payment">
                                        x
                                    </button>
                                </div>
                                <div className="form-grid modal-form-grid">
                                    <div className="form-field">
                                        <label htmlFor="payment-amount">Amount</label>
                                        <input
                                            id="payment-amount"
                                            value={paymentAmountDollars}
                                            onChange={(event) => setPaymentAmountDollars(event.target.value)}
                                            placeholder="50"
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label htmlFor="payment-date">Payment Date</label>
                                        <input
                                            id="payment-date"
                                            type="date"
                                            value={paymentDate}
                                            onChange={(event) => setPaymentDate(event.target.value)}
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label htmlFor="payment-method">Method</label>
                                        <select
                                            id="payment-method"
                                            value={paymentMethod}
                                            onChange={(event) => setPaymentMethod(event.target.value as PaymentMethod)}
                                        >
                                            {PAYMENT_METHODS.map((method) => (
                                                <option key={method} value={method}>
                                                    {method.replace("_", " ")}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="form-field">
                                        <label htmlFor="payment-note">Note</label>
                                        <input
                                            id="payment-note"
                                            value={paymentNote}
                                            onChange={(event) => setPaymentNote(event.target.value)}
                                            placeholder="Check number, card note"
                                        />
                                    </div>
                                    <div className="modal-actions">
                                        <button className="secondary-button" type="button" onClick={closeAddPayment} disabled={isPaymentSubmitting}>
                                            Cancel
                                        </button>
                                        <button className="primary-button" type="submit" disabled={isPaymentSubmitting}>
                                            {isPaymentSubmitting ? "Saving..." : "Save Payment"}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    )}
                </>
            ) : (
                <p className="empty-state">Invoice not found.</p>
            )}
        </>
    );
}
