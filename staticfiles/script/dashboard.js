const state = {
    employees: [],
    joinings: [],
    documents: [],
    billing: [],
    expenses: [],
    expenseCategories: [],
    expenseProducts: [],
};
let expenseCart = [];
let expenseCartChanged = false;
let joiningPhotoPreviewUrl = "";
const employeePrintSheet = document.getElementById("joining-print-sheet");
const joiningPrintSheetParent = employeePrintSheet.parentElement;

const sectionTitles = {
    overview: "Overview",
    employees: "Employees",
    joinings: "New joining",
    documents: "Documents",
    clients: "Clients",
    billing: "Billing",
    expenses: "Expenses",
};

const csrfToken = document.querySelector(".csrf-source input[name=csrfmiddlewaretoken]")?.value;
const toast = document.getElementById("toast");
let toastTimer;

function escapeHtml(value = "") {
    return String(value).replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    })[character]);
}

function showToast(message, isError = false) {
    toast.textContent = message;
    toast.classList.toggle("toast-error", isError);
    toast.classList.add("visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 3600);
}

function errorMessage(payload) {
    if (typeof payload === "string") return payload;
    if (payload && typeof payload === "object") {
        return Object.entries(payload)
            .map(([field, messages]) => `${field === "non_field_errors" ? "" : `${field}: `}${[].concat(messages).join(" ")}`)
            .join(" ");
    }
    return "The request could not be completed.";
}

async function api(path, options = {}) {
    const method = options.method || "GET";
    const headers = { Accept: "application/json", ...options.headers };
    const requestOptions = { method, headers, credentials: "same-origin" };
    if (options.body !== undefined) {
        if (options.body instanceof FormData) {
            requestOptions.body = options.body;
        } else {
            headers["Content-Type"] = "application/json";
            requestOptions.body = JSON.stringify(options.body);
        }
    }
    if (!["GET", "HEAD", "OPTIONS"].includes(method)) headers["X-CSRFToken"] = csrfToken;

    const response = await fetch(path, requestOptions);
    const payload = response.status === 204 ? null : await response.json();
    if (!response.ok) throw new Error(errorMessage(payload));
    return payload;
}

function emptyRow(columns, message) {
    return `<tr><td class="empty-cell" colspan="${columns}">${escapeHtml(message)}</td></tr>`;
}

function statusBadge(value) {
    const label = String(value || "unknown").replaceAll("_", " ");
    return `<span class="status-badge status-${escapeHtml(value)}">${escapeHtml(label)}</span>`;
}

function displayDate(value) {
    if (!value) return "—";
    return new Intl.DateTimeFormat("en", { day: "2-digit", month: "short", year: "numeric" })
        .format(new Date(`${value}T00:00:00`));
}

function inputDateToday() {
    const date = new Date();
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function employeeName(employee) {
    return employee ? `${employee.full_name} · ${employee.employee_id}` : "Unassigned employee";
}

function employeeDetailGrid(fields) {
    return fields.map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value || "—")}</dd></div>`).join("");
}

function employeeJoiningPrintData(employee, joining) {
    return {
        ...joining,
        employee: employee.id,
        employee_name: employee.full_name,
        application_date: joining?.application_date || "",
        joining_date: joining?.joining_date || "",
        nationality: joining?.nationality || employee.nationality || "",
        passport_number: joining?.passport_number || "",
        citizenship_number: joining?.citizenship_number || "",
        passport_expiry: joining?.passport_expiry || "",
        mobile_number: joining?.mobile_number || employee.phone || "",
        job_title: joining?.job_title || employee.job_title || "",
        client_name: employee.client_name || joining?.client_name || "",
        destination: employee.destination || joining?.destination || "",
        assigned_employee_number: joining?.assigned_employee_number || employee.employee_id,
        passport_photo_url: joining?.passport_photo_url || "",
    };
}

function openEmployeeDetails(id) {
    const employee = state.employees.find((item) => item.id === Number(id));
    if (!employee) return;
    const joining = state.joinings
        .filter((record) => record.employee === employee.id)
        .sort((first, second) => (second.joining_date || "").localeCompare(first.joining_date || ""))[0];
    const employeeFields = [
        ["Employee ID", employee.employee_id],
        ["Full name", employee.full_name],
        ["Phone", employee.phone],
        ["Email", employee.email],
        ["Nationality", employee.nationality],
        ["Job title", employee.job_title],
        ["Client", employee.client_name],
        ["Origin country", employee.origin_country],
        ["Destination", employee.destination],
        ["Status", employee.status?.replaceAll("_", " ")],
        ["Added", displayDate(employee.created_at?.slice(0, 10))],
        ["Last updated", displayDate(employee.updated_at?.slice(0, 10))],
    ];
    const joiningFields = joining ? [
        ["Application date", displayDate(joining.application_date)],
        ["Joining date", displayDate(joining.joining_date)],
        ["Father name", joining.father_name],
        ["City", joining.city],
        ["Visa status", joining.visa_status],
        ["Visa expiry", displayDate(joining.visa_expiry)],
        ["Passport number", joining.passport_number],
        ["Citizenship number", joining.citizenship_number],
        ["Passport expiry", displayDate(joining.passport_expiry)],
        ["Mobile", joining.mobile_number || employee.phone],
        ["Second mobile", joining.secondary_mobile_number],
        ["WhatsApp", joining.whatsapp_number],
        ["Second WhatsApp", joining.secondary_whatsapp_number],
        ["Home phone", joining.home_number],
        ["Second home phone", joining.secondary_home_number],
        ["Basic salary", joining.basic_salary],
        ["Commission", joining.commission_percent],
        ["Allowance", joining.allowance],
        ["Training period", joining.training_period],
        ["Starting date", displayDate(joining.starting_date)],
        ["End date", displayDate(joining.end_date)],
        ["Monthly target", joining.monthly_target],
        ["Visa charges", joining.visa_charges],
        ["HR name", joining.hr_name],
        ["HR phone", joining.hr_phone],
        ["Joining status", joining.status?.replaceAll("_", " ")],
    ] : [];
    const documents = state.documents.filter((document) => document.employee === employee.id);
    document.getElementById("employee-detail-title").textContent = employee.full_name;
    document.getElementById("employee-detail-subtitle").textContent = `${employee.employee_id} · ${employee.status.replaceAll("_", " ")}`;
    document.getElementById("employee-detail-grid").innerHTML = employeeDetailGrid(employeeFields);
    document.getElementById("employee-joining-grid").innerHTML = joining
        ? employeeDetailGrid(joiningFields)
        : `<p class="empty-note">No joining application is linked to this employee.</p>`;
    document.getElementById("employee-detail-documents").innerHTML = documents.length
        ? documents.map((document) => `<article class="employee-document-item"><a href="${escapeHtml(document.download_url)}">${escapeHtml(document.title)}</a><span>${escapeHtml(document.category)}</span></article>`).join("")
        : `<p class="empty-note">No employee documents have been added.</p>`;
    setJoiningPrintFields(employeeJoiningPrintData(employee, joining));
    document.getElementById("employee-print-sheet-slot").appendChild(employeePrintSheet);
    document.getElementById("employee-detail-overlay").hidden = false;
    document.getElementById("employee-detail-close").focus();
}

function closeEmployeeDetails() {
    document.getElementById("employee-detail-overlay").hidden = true;
    joiningPrintSheetParent.appendChild(employeePrintSheet);
}

function setJoiningPrintFields(joining) {
    const employee = state.employees.find((item) => item.id === Number(joining.employee));
    const values = {
        ...joining,
        employee_name: joining.employee_name || employee?.full_name || "",
        application_date: displayDate(joining.application_date),
        joining_date: displayDate(joining.joining_date),
        visa_expiry: displayDate(joining.visa_expiry),
        passport_expiry: displayDate(joining.passport_expiry),
        starting_date: displayDate(joining.starting_date),
        end_date: displayDate(joining.end_date),
    };
    for (const [name, value] of Object.entries(values)) {
        const field = document.querySelector(`[data-print-field="${name}"]`);
        if (field) field.textContent = value ?? "";
    }
    const image = document.getElementById("joining-print-photo-image");
    const placeholder = document.getElementById("joining-print-photo-placeholder");
    const photoUrl = joining.passport_photo_url || "";
    image.hidden = !photoUrl;
    placeholder.hidden = Boolean(photoUrl);
    if (photoUrl) image.src = photoUrl;
}

function printSavedJoining(id) {
    const joining = state.joinings.find((item) => item.id === Number(id));
    if (!joining) return;
    setJoiningPrintFields(joining);
    printJoiningSheet();
}

function printJoiningSheet() {
    const printingEmployeePreview = !joiningPrintSheetParent.contains(employeePrintSheet);
    document.body.classList.add("joining-print-mode");
    if (printingEmployeePreview) document.body.classList.add("employee-detail-print-mode");
    window.addEventListener("afterprint", () => {
        document.body.classList.remove("joining-print-mode", "employee-detail-print-mode");
    }, { once: true });
    window.print();
}

function printCurrentJoining() {
    const form = document.getElementById("joining-form");
    const values = Object.fromEntries(new FormData(form).entries());
    const employee = state.employees.find((item) => item.id === Number(values.employee));
    const joining = { ...values, employee_name: employee?.full_name || values.applicant_name || "" };
    const photo = form.elements.namedItem("passport_photo").files[0];
    joining.passport_photo_url = photo ? joiningPhotoPreviewUrl : "";
    setJoiningPrintFields(joining);
    printJoiningSheet();
}

function renderEmployeeTable(employees) {
    const body = document.getElementById("employees-table");
    document.getElementById("employee-result-count").textContent = `${employees.length} ${employees.length === 1 ? "employee" : "employees"}`;
    body.innerHTML = employees.length ? employees.map((employee) => `
        <tr>
            <td><span class="table-primary">${escapeHtml(employee.full_name)}</span><span class="table-secondary">${escapeHtml(employee.employee_id)}</span></td>
            <td><span class="table-primary">${escapeHtml(employee.phone)}</span><span class="table-secondary">${escapeHtml(employee.email || "No email")}</span></td>
            <td>${escapeHtml(employee.client_name || "—")}</td>
            <td>${statusBadge(employee.status)}</td>
            <td class="row-actions"><button class="row-action danger-action" data-delete="/api/employees/${employee.id}/" aria-label="Delete ${escapeHtml(employee.full_name)}">Delete</button></td>
        </tr>`).join("") : emptyRow(5, "No employee records yet.");
}

function renderEmployees() {
    renderEmployeeTable(state.employees);
    const options = state.employees.map((employee) => `<option value="${employee.id}">${escapeHtml(employeeName(employee))}</option>`).join("");
    for (const id of ["joining-employee", "document-employee"]) {
        const select = document.getElementById(id);
        const selected = select.value;
        const emptyLabel = id === "joining-employee" ? "Create a new employee" : "Select employee";
        select.innerHTML = `<option value="">${emptyLabel}</option>${options}`;
        select.value = selected;
    }
    const recent = [...state.employees].slice(0, 5);
    document.getElementById("recent-employees").innerHTML = recent.length ? recent.map((employee) => `
        <tr><td><span class="table-primary">${escapeHtml(employee.full_name)}</span><span class="table-secondary">${escapeHtml(employee.employee_id)}</span></td><td>${escapeHtml(employee.client_name || "—")}</td><td>${statusBadge(employee.status)}</td></tr>`).join("") : emptyRow(3, "Employee records will appear here.");
}

function renderJoinings() {
    const body = document.getElementById("joinings-table");
    body.innerHTML = state.joinings.length ? state.joinings.map((joining) => `
        <tr>
            <td><span class="table-primary">${escapeHtml(joining.employee_name)}</span><span class="table-secondary">${escapeHtml(joining.employee_id)}</span></td>
            <td>${escapeHtml(joining.client_name)}</td>
            <td><span class="table-primary">${escapeHtml(joining.hiring_person_name)}</span><span class="table-secondary">${escapeHtml(joining.hiring_person_employee_id || "No EMP ID")}</span></td>
            <td>${displayDate(joining.joining_date)}</td>
            <td>${statusBadge(joining.status)}</td>
            <td class="row-actions"><button class="row-action" data-print-joining="${joining.id}" aria-label="Print joining form for ${escapeHtml(joining.employee_name)}">Print</button><button class="row-action danger-action" data-delete="/api/joinings/${joining.id}/" aria-label="Delete joining for ${escapeHtml(joining.employee_name)}">Delete</button></td>
        </tr>`).join("") : emptyRow(6, "No joining records yet.");

    const recent = state.joinings.slice(0, 4);
    document.getElementById("recent-joinings").innerHTML = recent.length ? recent.map((joining) => `
        <article class="activity-item"><span class="activity-mark">↗</span><div><strong>${escapeHtml(joining.employee_name)}</strong><span>${escapeHtml(joining.client_name)} · ${displayDate(joining.joining_date)}</span></div>${statusBadge(joining.status)}</article>`).join("") : `<p class="empty-note">New hiring activity will appear here.</p>`;
}

function renderDocuments() {
    const body = document.getElementById("documents-table");
    body.innerHTML = state.documents.length ? state.documents.map((document) => {
        const employee = state.employees.find((item) => item.id === document.employee);
        return `<tr>
            <td><a class="table-primary file-link" href="${escapeHtml(document.download_url)}">${escapeHtml(document.title)}</a></td>
            <td>${escapeHtml(employeeName(employee))}</td>
            <td>${escapeHtml(document.category)}</td>
            <td>${displayDate(document.uploaded_at?.slice(0, 10))}</td>
            <td class="row-actions"><button class="row-action danger-action" data-delete="/api/documents/${document.id}/" aria-label="Delete ${escapeHtml(document.title)}">Delete</button></td>
        </tr>`;
    }).join("") : emptyRow(5, "Uploaded employee documents will appear here.");
}

function renderClients() {
    const clients = new Map();
    for (const employee of state.employees) {
        if (!employee.client_name) continue;
        const account = clients.get(employee.client_name) || { employees: [], joinings: 0 };
        account.employees.push(employee);
        clients.set(employee.client_name, account);
    }
    for (const joining of state.joinings) {
        const account = clients.get(joining.client_name) || { employees: [], joinings: 0 };
        account.joinings += 1;
        clients.set(joining.client_name, account);
    }
    const rows = [...clients.entries()].sort(([first], [second]) => first.localeCompare(second));
    document.getElementById("clients-list").innerHTML = rows.length ? rows.map(([name, account], index) => `
        <article class="client-row"><span class="client-index">${String(index + 1).padStart(2, "0")}</span><div class="client-name"><h3>${escapeHtml(name)}</h3><span>${account.employees.length} assigned ${account.employees.length === 1 ? "employee" : "employees"}</span></div><div class="client-summary"><span class="client-count">${account.joinings}</span><span>joining records</span></div><button class="text-button" data-go="employees">View directory <span aria-hidden="true">→</span></button></article>`).join("") : `<div class="panel empty-panel">Client accounts appear when a client is assigned to an employee or joining record.</div>`;
}

function renderBilling() {
    const body = document.getElementById("billing-table");
    body.innerHTML = state.billing.length ? state.billing.map((invoice) => `
        <tr>
            <td><span class="table-primary">${escapeHtml(invoice.invoice_number)}</span><span class="table-secondary">${displayDate(invoice.bill_date)}</span></td>
            <td>${escapeHtml(invoice.client_name)}</td>
            <td>${escapeHtml(invoice.description)}</td>
            <td class="amount-cell">${escapeHtml(invoice.currency)} ${Number(invoice.amount).toLocaleString("en", { minimumFractionDigits: 2 })}</td>
            <td>${statusBadge(invoice.status)}</td>
            <td class="row-actions"><button class="row-action danger-action" data-delete="/api/billing/${invoice.id}/" aria-label="Delete invoice ${escapeHtml(invoice.invoice_number)}">Delete</button></td>
        </tr>`).join("") : emptyRow(6, "Billing records will appear here.");
}

function renderExpenses(search = "") {
    const body = document.getElementById("expenses-table");
    const query = search.trim().toLowerCase();
    const expenses = state.expenses.filter((expense) => !query || [
        expense.reference_number,
        expense.vendor_name,
        expense.category,
        expense.description,
    ].some((value) => String(value || "").toLowerCase().includes(query)));
    body.innerHTML = expenses.length ? expenses.map((expense) => `
        <tr>
            <td><span class="table-primary">${escapeHtml(expense.reference_number || "No reference")}</span><span class="table-secondary">${displayDate(expense.bill_date)}</span></td>
            <td>${escapeHtml(expense.vendor_name)}</td>
            <td>${escapeHtml(expense.category)}</td>
            <td>${expense.items.length ? expense.items.map((item) => `<span class="table-primary">${escapeHtml(item.product_name)}</span><span class="table-secondary">x ${escapeHtml(item.quantity)}</span>`).join("") : escapeHtml(expense.description)}</td>
            <td class="amount-cell">${escapeHtml(expense.currency)} ${Number(expense.amount).toLocaleString("en", { minimumFractionDigits: 2 })}</td>
            <td><span class="table-primary">${displayDate(expense.due_date)}</span>${expense.paid_date ? `<span class="table-secondary">Paid ${displayDate(expense.paid_date)}</span>` : ""}</td>
            <td>${statusBadge(expense.status)}</td>
            <td class="row-actions"><button class="row-action" data-edit-expense="${expense.id}" aria-label="Edit expense bill from ${escapeHtml(expense.vendor_name)}">Edit</button><button class="row-action danger-action" data-delete="/api/expenses/${expense.id}/" aria-label="Delete expense bill from ${escapeHtml(expense.vendor_name)}">Delete</button></td>
        </tr>`).join("") : emptyRow(8, query ? "No matching expense bills." : "Expense bills will appear here.");
}

function renderExpenseCatalog() {
    const categorySelect = document.getElementById("expense-product-category");
    const categoryFilter = document.getElementById("expense-category-filter");
    const selectedCategory = categorySelect.value;
    const selectedFilter = categoryFilter.value;
    const categoryOptions = state.expenseCategories.map((category) =>
        `<option value="${category.id}">${escapeHtml(category.name)}</option>`
    ).join("");
    categorySelect.innerHTML = categoryOptions || `<option value="">Add a category first</option>`;
    categorySelect.value = state.expenseCategories.some((category) => String(category.id) === selectedCategory)
        ? selectedCategory
        : String(state.expenseCategories[0]?.id || "");
    categoryFilter.innerHTML = `<option value="">All categories</option>${categoryOptions}`;
    categoryFilter.value = state.expenseCategories.some((category) => String(category.id) === selectedFilter)
        ? selectedFilter
        : "";
    document.getElementById("expense-category-list").innerHTML = state.expenseCategories.length
        ? state.expenseCategories.map((category) => `<span class="category-chip">${escapeHtml(category.name)}</span>`).join("")
        : `<p class="empty-note">Add a category to start building your catalog.</p>`;

    const query = document.getElementById("expense-product-search").value.trim().toLowerCase();
    const categoryId = categoryFilter.value;
    const products = state.expenseProducts.filter((product) =>
        (!categoryId || String(product.category) === categoryId)
        && (!query || `${product.name} ${product.category_name}`.toLowerCase().includes(query))
    );
    document.getElementById("expense-products-table").innerHTML = products.length
        ? products.map((product) => `<tr>
            <td><span class="table-primary">${escapeHtml(product.name)}</span></td>
            <td>${escapeHtml(product.category_name)}</td>
            <td class="amount-cell">${escapeHtml(product.currency)} ${Number(product.unit_price).toLocaleString("en", { minimumFractionDigits: 2 })}</td>
            <td class="row-actions"><button class="row-action" data-add-product="${product.id}" aria-label="Add ${escapeHtml(product.name)} to bill">Add</button></td>
        </tr>`).join("")
        : emptyRow(4, query || categoryId ? "No matching products." : "Add products to your catalog.");
}

function renderExpenseCart() {
    const body = document.getElementById("expense-cart");
    const form = document.getElementById("expense-form");
    const lines = expenseCart.map((line) => {
        const productId = Number(line.product ?? line.product_id);
        const product = state.expenseProducts.find((item) => item.id === productId);
        return { ...line, productId, product };
    });
    const total = lines.reduce((sum, line) => {
        const price = Number(line.product?.unit_price ?? line.unit_price ?? 0);
        return sum + Math.round(price * Number(line.quantity) * 100) / 100;
    }, 0);
    const legacyExpense = !lines.length && form.dataset.recordId && !expenseCartChanged
        ? state.expenses.find((expense) => expense.id === Number(form.dataset.recordId))
        : null;
    const displayedTotal = legacyExpense ? Number(legacyExpense.amount) : total;
    const currency = lines[0]?.product?.currency || lines[0]?.currency || legacyExpense?.currency || "AED";
    document.getElementById("cart-item-count").textContent = `${lines.length} ${lines.length === 1 ? "item" : "items"}`;
    document.getElementById("expense-total").textContent = `${currency} ${displayedTotal.toLocaleString("en", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    body.innerHTML = lines.length ? lines.map((line) => {
        const name = line.product?.name || line.product_name || "Product unavailable";
        const price = Number(line.product?.unit_price ?? line.unit_price ?? 0);
        return `<tr>
            <td><span class="table-primary">${escapeHtml(name)}</span><span class="table-secondary">${escapeHtml(line.product?.category_name || line.category_name || "")}</span></td>
            <td>${escapeHtml(line.product?.currency || line.currency || currency)} ${price.toFixed(2)}</td>
            <td><input class="cart-quantity" data-cart-quantity="${line.productId}" type="number" min="0.01" step="0.01" value="${escapeHtml(line.quantity)}" aria-label="Quantity for ${escapeHtml(name)}"></td>
            <td class="amount-cell">${escapeHtml(line.product?.currency || line.currency || currency)} ${(price * Number(line.quantity)).toLocaleString("en", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            <td class="row-actions"><button class="row-action danger-action" data-remove-cart-item="${line.productId}" aria-label="Remove ${escapeHtml(name)} from bill">Remove</button></td>
        </tr>`;
    }).join("") : emptyRow(5, legacyExpense ? "This saved bill has no product lines." : "Add products from the catalog to this bill.");
}

function renderOverview() {
    const clients = new Set([
        ...state.employees.map((employee) => employee.client_name),
        ...state.joinings.map((joining) => joining.client_name),
    ].filter(Boolean));
    const openJoinings = state.joinings.filter((joining) => ["new", "in_progress"].includes(joining.status));
    const unpaid = state.billing.filter((invoice) => ["sent", "overdue"].includes(invoice.status));
    const totals = unpaid.reduce((sum, invoice) => sum + Number(invoice.amount), 0);
    const currency = unpaid[0]?.currency || "AED";
    document.getElementById("stat-employees").textContent = state.employees.length;
    document.getElementById("stat-joinings").textContent = openJoinings.length;
    document.getElementById("stat-clients").textContent = clients.size;
    document.getElementById("stat-billing").textContent = `${currency} ${totals.toLocaleString("en", { maximumFractionDigits: 0 })}`;
}

async function refresh() {
    const [employees, joinings, documents, billing, expenses, expenseCategories, expenseProducts] = await Promise.all([
        api("/api/employees/"),
        api("/api/joinings/"),
        api("/api/documents/"),
        api("/api/billing/"),
        api("/api/expenses/"),
        api("/api/expense-categories/"),
        api("/api/expense-products/"),
    ]);
    Object.assign(state, { employees, joinings, documents, billing, expenses, expenseCategories, expenseProducts });
    renderEmployees();
    renderJoinings();
    renderDocuments();
    renderClients();
    renderBilling();
    renderExpenses(document.getElementById("expense-search").value);
    renderExpenseCatalog();
    renderExpenseCart();
    renderOverview();
}

function navigate(section) {
    if (!sectionTitles[section]) return;
    document.querySelectorAll(".page-section").forEach((panel) => {
        const active = panel.id === `section-${section}`;
        panel.hidden = !active;
        panel.classList.toggle("active", active);
    });
    document.querySelectorAll(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.section === section));
    document.getElementById("page-title").textContent = sectionTitles[section];
    document.getElementById("crumb-current").textContent = sectionTitles[section].toUpperCase();
}

async function submitForm(form, endpoint, options = {}) {
    const method = options.method || "POST";
    const body = options.multipart ? new FormData(form) : Object.fromEntries(new FormData(form).entries());
    await api(endpoint, { method, body });
    form.reset();
    if (options.afterReset) options.afterReset();
    await refresh();
    showToast(options.success || "Saved successfully.");
}

function resetEmployeeForm() {
    const form = document.getElementById("employee-form");
    form.reset();
    delete form.dataset.recordId;
    document.getElementById("employee-form-title").textContent = "Add employee";
    document.getElementById("employee-submit").textContent = "Save employee";
    document.getElementById("employee-cancel").hidden = true;
}

function editEmployee(id) {
    const employee = state.employees.find((item) => item.id === Number(id));
    if (!employee) return;
    const form = document.getElementById("employee-form");
    for (const [key, value] of Object.entries(employee)) {
        if (form.elements.namedItem(key)) form.elements.namedItem(key).value = value ?? "";
    }
    form.dataset.recordId = employee.id;
    document.getElementById("employee-form-title").textContent = `Edit ${employee.employee_id}`;
    document.getElementById("employee-submit").textContent = "Update employee";
    document.getElementById("employee-cancel").hidden = false;
    form.scrollIntoView({ behavior: "smooth", block: "start" });
    form.elements.namedItem("full_name").focus({ preventScroll: true });
}

function resetExpenseForm() {
    const form = document.getElementById("expense-form");
    form.reset();
    delete form.dataset.recordId;
    expenseCart = [];
    expenseCartChanged = false;
    document.getElementById("expense-form-title").textContent = "New expense bill";
    document.getElementById("expense-submit").textContent = "Save expense bill";
    document.getElementById("expense-cancel").hidden = true;
    renderExpenseCart();
}

function editExpense(id) {
    const expense = state.expenses.find((item) => item.id === Number(id));
    if (!expense) return;
    const form = document.getElementById("expense-form");
    for (const [key, value] of Object.entries(expense)) {
        if (form.elements.namedItem(key)) form.elements.namedItem(key).value = value ?? "";
    }
    expenseCart = expense.items.map((item) => ({
        product: item.product,
        product_name: item.product_name,
        quantity: item.quantity,
        unit_price: item.unit_price,
    })).filter((item) => item.product);
    expenseCartChanged = false;
    form.dataset.recordId = expense.id;
    document.getElementById("expense-form-title").textContent = `Edit ${expense.reference_number || "expense bill"}`;
    document.getElementById("expense-submit").textContent = "Update expense bill";
    document.getElementById("expense-cancel").hidden = false;
    renderExpenseCart();
    form.scrollIntoView({ behavior: "smooth", block: "start" });
    form.elements.namedItem("vendor_name").focus({ preventScroll: true });
}

function addProductToBill(productId) {
    const product = state.expenseProducts.find((item) => item.id === Number(productId));
    if (!product) return;
    const currentCurrency = expenseCart[0]
        ? state.expenseProducts.find((item) => item.id === Number(expenseCart[0].product))?.currency
        : product.currency;
    if (currentCurrency && currentCurrency !== product.currency) {
        showToast("Products on one bill must use the same currency.", true);
        return;
    }
    const line = expenseCart.find((item) => Number(item.product) === product.id);
    if (line) line.quantity = (Number(line.quantity) + 1).toFixed(2);
    else expenseCart.push({ product: product.id, quantity: "1.00" });
    expenseCartChanged = true;
    renderExpenseCart();
}

document.querySelectorAll("[data-section]").forEach((button) => {
    button.addEventListener("click", () => navigate(button.dataset.section));
});

document.addEventListener("click", async (event) => {
    const navigation = event.target.closest("[data-go]");
    if (navigation) navigate(navigation.dataset.go);

    const editButton = event.target.closest("[data-edit-employee]");
    if (editButton) editEmployee(editButton.dataset.editEmployee);

    const editExpenseButton = event.target.closest("[data-edit-expense]");
    if (editExpenseButton) editExpense(editExpenseButton.dataset.editExpense);

    const printJoiningButton = event.target.closest("[data-print-joining]");
    if (printJoiningButton) printSavedJoining(printJoiningButton.dataset.printJoining);

    const addProductButton = event.target.closest("[data-add-product]");
    if (addProductButton) addProductToBill(addProductButton.dataset.addProduct);

    const removeCartItemButton = event.target.closest("[data-remove-cart-item]");
    if (removeCartItemButton) {
        expenseCart = expenseCart.filter((item) => Number(item.product) !== Number(removeCartItemButton.dataset.removeCartItem));
        expenseCartChanged = true;
        renderExpenseCart();
    }

    const deleteButton = event.target.closest("[data-delete]");
    if (deleteButton && window.confirm("Delete this record? This cannot be undone.")) {
        try {
            await api(deleteButton.dataset.delete, { method: "DELETE" });
            await refresh();
            showToast("Record deleted.");
        } catch (error) {
            showToast(error.message, true);
        }
    }
});

const employeeForm = document.getElementById("employee-form");
if (employeeForm) {
    employeeForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const id = form.dataset.recordId;
        try {
            await submitForm(form, id ? `/api/employees/${id}/` : "/api/employees/", {
                method: id ? "PATCH" : "POST",
                success: id ? "Employee updated." : "Employee added.",
                afterReset: resetEmployeeForm,
            });
        } catch (error) {
            showToast(error.message, true);
        }
    });

    const employeeCancel = document.getElementById("employee-cancel");
    if (employeeCancel) employeeCancel.addEventListener("click", resetEmployeeForm);
    employeeForm.addEventListener("reset", () => {
        window.setTimeout(() => {
            if (!employeeForm.dataset.recordId) {
                employeeForm.elements.namedItem("origin_country").value = "Nepal";
                employeeForm.elements.namedItem("destination").value = "Dubai, UAE";
            }
        });
    });
}

document.getElementById("joining-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await submitForm(event.currentTarget, "/api/joinings/", { multipart: true, success: "Joining record saved." });
    } catch (error) {
        showToast(error.message, true);
    }
});

document.getElementById("print-current-joining").addEventListener("click", printCurrentJoining);
document.querySelector("#joining-form input[name='passport_photo']").addEventListener("change", (event) => {
    const photo = event.currentTarget.files[0];
    const preview = document.getElementById("joining-photo-preview");
    const placeholder = document.querySelector(".joining-photo-frame span");
    if (joiningPhotoPreviewUrl) URL.revokeObjectURL(joiningPhotoPreviewUrl);
    joiningPhotoPreviewUrl = photo ? URL.createObjectURL(photo) : "";
    preview.hidden = !joiningPhotoPreviewUrl;
    placeholder.hidden = Boolean(joiningPhotoPreviewUrl);
    if (joiningPhotoPreviewUrl) preview.src = joiningPhotoPreviewUrl;
});

document.getElementById("joining-form").addEventListener("reset", () => {
    window.setTimeout(() => {
        if (joiningPhotoPreviewUrl) URL.revokeObjectURL(joiningPhotoPreviewUrl);
        joiningPhotoPreviewUrl = "";
        const preview = document.getElementById("joining-photo-preview");
        preview.removeAttribute("src");
        preview.hidden = true;
        document.querySelector(".joining-photo-frame span").hidden = false;
        document.querySelector("#joining-form input[name='application_date']").value = inputDateToday();
    });
});

document.getElementById("joining-employee").addEventListener("change", (event) => {
    const employee = state.employees.find((item) => item.id === Number(event.currentTarget.value));
    if (!employee) return;
    const form = document.getElementById("joining-form");
    form.elements.namedItem("applicant_name").value = employee.full_name;
    for (const [field, value] of [["nationality", employee.nationality], ["job_title", employee.job_title], ["client_name", employee.client_name]]) {
        const input = form.elements.namedItem(field);
        if (value && !input.value) input.value = value;
    }
});

document.getElementById("document-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await submitForm(event.currentTarget, "/api/documents/", { multipart: true, success: "Document uploaded." });
    } catch (error) {
        showToast(error.message, true);
    }
});

document.getElementById("billing-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await submitForm(event.currentTarget, "/api/billing/", { success: "Billing record saved." });
    } catch (error) {
        showToast(error.message, true);
    }
});

document.getElementById("expense-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const id = form.dataset.recordId;
    if (!expenseCart.length && (!id || expenseCartChanged)) {
        showToast("Add at least one product to the bill.", true);
        return;
    }
    try {
        const payload = Object.fromEntries(new FormData(form).entries());
        if (!id || expenseCartChanged) {
            payload.items = expenseCart.map((item) => ({
                product: Number(item.product),
                quantity: item.quantity,
            }));
        }
        await api(id ? `/api/expenses/${id}/` : "/api/expenses/", {
            method: id ? "PATCH" : "POST",
            body: payload,
        });
        resetExpenseForm();
        await refresh();
        showToast(id ? "Expense bill updated." : "Expense bill saved.");
    } catch (error) {
        showToast(error.message, true);
    }
});

document.getElementById("expense-cancel").addEventListener("click", resetExpenseForm);

document.getElementById("expense-cart").addEventListener("change", (event) => {
    const quantityInput = event.target.closest("[data-cart-quantity]");
    if (!quantityInput) return;
    const quantity = Number(quantityInput.value);
    if (!Number.isFinite(quantity) || quantity <= 0) {
        showToast("Product quantity must be greater than zero.", true);
        renderExpenseCart();
        return;
    }
    const line = expenseCart.find((item) => Number(item.product) === Number(quantityInput.dataset.cartQuantity));
    if (line) {
        line.quantity = quantity.toFixed(2);
        expenseCartChanged = true;
        renderExpenseCart();
    }
});

document.getElementById("expense-category-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await submitForm(event.currentTarget, "/api/expense-categories/", { success: "Category added." });
    } catch (error) {
        showToast(error.message, true);
    }
});

document.getElementById("expense-product-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await submitForm(event.currentTarget, "/api/expense-products/", { success: "Product added to catalog." });
    } catch (error) {
        showToast(error.message, true);
    }
});

document.getElementById("expense-category-filter").addEventListener("change", renderExpenseCatalog);
document.getElementById("expense-product-search").addEventListener("input", renderExpenseCatalog);

document.getElementById("expense-search").addEventListener("input", (event) => {
    renderExpenses(event.target.value);
});

let searchTimer;
document.getElementById("employee-search").addEventListener("input", (event) => {
    window.clearTimeout(searchTimer);
    const search = event.target.value.trim();
    searchTimer = window.setTimeout(async () => {
        try {
            const results = search ? await api(`/api/employees/?search=${encodeURIComponent(search)}`) : state.employees;
            renderEmployeeTable(results);
        } catch (error) {
            showToast(error.message, true);
        }
    }, 180);
});

document.getElementById("joining-search").addEventListener("input", (event) => {
    window.clearTimeout(searchTimer);
    const search = event.target.value.trim();
    searchTimer = window.setTimeout(async () => {
        try {
            const results = search ? await api(`/api/joinings/?search=${encodeURIComponent(search)}`) : state.joinings;
            const previous = state.joinings;
            state.joinings = results;
            renderJoinings();
            state.joinings = previous;
        } catch (error) {
            showToast(error.message, true);
        }
    }, 180);
});

document.getElementById("print-billing").addEventListener("click", () => window.print());
document.getElementById("print-expenses").addEventListener("click", () => window.print());
document.querySelector("[data-go='employees']")?.addEventListener("click", () => navigate("employees"));
document.getElementById("today-date").textContent = new Intl.DateTimeFormat("en", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
}).format(new Date());
document.querySelector("#joining-form input[name='application_date']").value = inputDateToday();

refresh().catch((error) => showToast(error.message, true));