export function digitsOnly(value: string) {
    return value.replace(/\D/g, "");
}

export function isValidCustomerPhone(phone: string) {
    return phone === "" || phone.length === 10;
}

export function formatPhoneNumber(phone: string | null | undefined) {
    if (!phone) {
        return "-";
    }

    const digits = digitsOnly(phone);
    if (digits.length === 10) {
        return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
    }

    return digits || "-";
}
