const API_BASE = "/api/v1";
const TOKEN_KEY = "hotelsys_access_token";
const ACCOUNT_KEY = "hotelsys_current_account";

const ROOM_STATUSES = ["空闲", "已预定", "已入住", "待清扫", "停用"];
const RESERVATION_STATUSES = ["未入住", "已入住", "已取消"];
const APPROVAL_STATUSES = ["待审核", "已启用", "已驳回", "已停用"];
const CLEAN_STATUSES = ["待清扫", "清扫中", "已完成"];
const PUBLIC_PERMISSIONS = [
  { permissionId: 1, permissionName: "管理员" },
  { permissionId: 2, permissionName: "前台工作人员" },
  { permissionId: 3, permissionName: "保洁员" },
  { permissionId: 4, permissionName: "审计员" }
];

const navItems = [
  { id: "dashboard", label: "首页总览", kicker: "Dashboard", title: "首页总览" },
  { id: "auth", label: "登录注册", kicker: "Auth", title: "登录与账号注册" },
  { id: "accounts", label: "账号审核", kicker: "Accounts", title: "账号审核与权限" },
  { id: "customers", label: "客户管理", kicker: "Customers", title: "客户与折扣管理" },
  { id: "rooms", label: "客房管理", kicker: "Rooms", title: "客房类型与客房管理" },
  { id: "reservations", label: "预定管理", kicker: "Reservations", title: "客房预定管理" },
  { id: "checkins", label: "入住结账", kicker: "Check-ins", title: "入住、换房与结账" },
  { id: "cleaning", label: "清扫任务", kicker: "Cleaning", title: "清扫任务管理" },
  { id: "audit", label: "操作审计", kicker: "Audit", title: "操作日志查询" },
  { id: "frontendTasks", label: "前端任务", kicker: "Tasks", title: "前端对接任务清单" }
];

const ROLE_VIEW_ACCESS = {
  管理员: ["dashboard", "accounts", "customers", "rooms", "reservations", "checkins", "cleaning", "audit", "frontendTasks"],
  前台工作人员: ["dashboard", "customers", "rooms", "reservations", "checkins", "cleaning"],
  保洁员: ["dashboard", "cleaning"],
  审计员: ["dashboard", "customers", "rooms", "checkins", "audit"]
};

let currentAccount = readJson(ACCOUNT_KEY, null);
let accessToken = localStorage.getItem(TOKEN_KEY) || "";
let activeView = accessToken && currentAccount ? "dashboard" : "auth";
let loadTicket = 0;

const dataStore = {
  permissions: [],
  accounts: [],
  discounts: [],
  customers: [],
  roomTypes: [],
  rooms: [],
  availableRooms: [],
  roomOverview: [],
  reservations: [],
  checkIns: [],
  checkouts: [],
  cleaningTasks: [],
  operationTypes: [],
  operationLogs: []
};

function readJson(key, fallback) {
  const raw = localStorage.getItem(key);
  if (!raw) return fallback;
  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function init() {
  localStorage.removeItem("hotelsys_spec_frontend_state_v1");
  localStorage.removeItem("hotelsys_use_real_api");
  document.getElementById("navList").addEventListener("click", event => {
    const button = event.target.closest("[data-view]");
    if (!button) return;
    activeView = button.dataset.view;
    render();
  });
  document.getElementById("logoutSession").addEventListener("click", logoutSession);
  render();
}

function render(options = {}) {
  const { load = true } = options;
  guardActiveView();
  renderNav();

  document.querySelector(".sidebar").classList.toggle("logged-out", !isAuthenticated());
  const nav = navItems.find(item => item.id === activeView) || navItems[0];
  document.getElementById("pageKicker").textContent = nav.kicker;
  document.getElementById("pageTitle").textContent = nav.title;
  document.getElementById("apiModeLabel").textContent = "真实接口";
  document.getElementById("apiBaseLabel").textContent = API_BASE;
  document.getElementById("accountChip").textContent = currentAccount
    ? `${currentAccount.accountName} · ${currentAccount.permissionName}`
    : "未登录";
  document.getElementById("logoutSession").classList.toggle("hidden", !isAuthenticated());

  const views = {
    dashboard: renderDashboard,
    auth: renderAuth,
    accounts: renderAccounts,
    customers: renderCustomers,
    rooms: renderRooms,
    reservations: renderReservations,
    checkins: renderCheckIns,
    cleaning: renderCleaning,
    audit: renderAudit,
    frontendTasks: renderFrontendTasks
  };

  document.getElementById("viewRoot").innerHTML = views[activeView]();
  document.querySelectorAll(".nav-button").forEach(button => {
    button.classList.toggle("active", button.dataset.view === activeView);
  });
  bindEvents();

  if (load && isAuthenticated() && activeView !== "frontendTasks") {
    loadCurrentView(activeView);
  }
}

function renderNav() {
  const nav = document.getElementById("navList");
  nav.innerHTML = getVisibleNavItems().map(item => `
    <button class="nav-button" data-view="${item.id}" type="button">
      <span>${item.label}</span>
    </button>
  `).join("");
}

function isAuthenticated() {
  return Boolean(accessToken && currentAccount);
}

function currentRole() {
  return currentAccount?.permissionName || "";
}

function allowedViews() {
  if (!isAuthenticated()) return ["auth"];
  return ROLE_VIEW_ACCESS[currentRole()] || ["dashboard"];
}

function canAccessView(viewId) {
  return allowedViews().includes(viewId);
}

function guardActiveView() {
  if (!isAuthenticated()) {
    activeView = "auth";
    return;
  }
  if (activeView === "auth" || !canAccessView(activeView)) {
    activeView = allowedViews()[0] || "dashboard";
  }
}

function getVisibleNavItems() {
  if (!isAuthenticated()) return [];
  const allowed = allowedViews();
  return navItems.filter(item => item.id !== "auth" && allowed.includes(item.id));
}

function logoutSession() {
  logoutWithoutToast();
  clearDataStore();
  render();
  toast("已退出登录", "业务页面已锁定，请重新登录后继续操作。");
}

function logoutWithoutToast() {
  accessToken = "";
  currentAccount = null;
  activeView = "auth";
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ACCOUNT_KEY);
}

function clearDataStore() {
  Object.keys(dataStore).forEach(key => {
    dataStore[key] = [];
  });
}

function isAdmin() {
  return currentRole() === "管理员";
}

function isFrontDesk() {
  return currentRole() === "前台工作人员";
}

function isCleaner() {
  return currentRole() === "保洁员";
}

function isAuditor() {
  return currentRole() === "审计员";
}

function canManageAccounts() {
  return isAdmin();
}

function canManageCustomers() {
  return isAdmin() || isFrontDesk();
}

function canManageRooms() {
  return isAdmin();
}

function canManageReservations() {
  return isAdmin() || isFrontDesk();
}

function canManageCheckIns() {
  return isAdmin() || isFrontDesk();
}

function canHandleCleaning() {
  return isCleaner();
}

function forbidden() {
  toast("无权限", "当前角色不能执行这个操作。", "error");
}

async function loadCurrentView(viewId) {
  const ticket = ++loadTicket;
  try {
    const loaders = {
      dashboard: loadDashboardData,
      accounts: loadAccountsData,
      customers: loadCustomersData,
      rooms: loadRoomsData,
      reservations: loadReservationsData,
      checkins: loadCheckInsData,
      cleaning: loadCleaningData,
      audit: loadAuditData,
      auth: async () => {}
    };
    await (loaders[viewId] || loaders.dashboard)();
    if (ticket === loadTicket && activeView === viewId) render({ load: false });
  } catch (error) {
    if (ticket === loadTicket) toast("数据加载失败", error.message, "error");
  }
}

async function loadDashboardData() {
  const [customers, rooms, reservations, checkIns, checkouts, cleaningTasks, overview] = await Promise.all([
    safeItems("/customers", { pageSize: 100 }),
    safeItems("/rooms", { pageSize: 100 }),
    safeItems("/reservations", { pageSize: 100 }),
    safeItems("/check-ins", { pageSize: 100 }),
    safeItems("/checkouts", { pageSize: 100 }),
    safeItems("/cleaning-tasks", { pageSize: 100 }),
    safeItems("/rooms/status-overview")
  ]);
  dataStore.customers = customers;
  dataStore.rooms = rooms;
  dataStore.reservations = reservations;
  dataStore.checkIns = checkIns;
  dataStore.checkouts = checkouts;
  dataStore.cleaningTasks = cleaningTasks;
  dataStore.roomOverview = overview;
}

async function loadAccountsData(query = {}) {
  const [accounts, permissions] = await Promise.all([
    requireItems("/accounts", { pageSize: 100, ...query }),
    requireList("/permissions")
  ]);
  dataStore.accounts = accounts;
  dataStore.permissions = permissions;
}

async function loadCustomersData() {
  const [customers, discounts] = await Promise.all([
    requireItems("/customers", { pageSize: 100 }),
    canManageCustomers() ? requireList("/discounts") : safeList("/discounts")
  ]);
  dataStore.customers = customers;
  dataStore.discounts = discounts;
}

async function loadRoomsData(query = {}) {
  const [rooms, roomTypes] = await Promise.all([
    requireItems("/rooms", { pageSize: 100, ...query }),
    safeList("/room-types")
  ]);
  dataStore.rooms = rooms;
  dataStore.roomTypes = roomTypes;
}

async function loadReservationsData(query = {}) {
  const [reservations, customers, roomTypes] = await Promise.all([
    requireItems("/reservations", { pageSize: 100, ...query }),
    requireItems("/customers", { pageSize: 100 }),
    requireList("/room-types")
  ]);
  dataStore.reservations = reservations;
  dataStore.customers = customers;
  dataStore.roomTypes = roomTypes;
}

async function loadCheckInsData() {
  const [checkIns, checkouts, customers, rooms, availableRooms, roomTypes] = await Promise.all([
    requireItems("/check-ins", { pageSize: 100 }),
    requireItems("/checkouts", { pageSize: 100 }),
    safeItems("/customers", { pageSize: 100 }),
    safeItems("/rooms", { pageSize: 100 }),
    canManageCheckIns() ? safeItems("/rooms/available", { pageSize: 100 }) : Promise.resolve([]),
    safeList("/room-types")
  ]);
  dataStore.checkIns = checkIns;
  dataStore.checkouts = checkouts;
  dataStore.customers = customers;
  dataStore.rooms = rooms;
  dataStore.availableRooms = availableRooms;
  dataStore.roomTypes = roomTypes;
}

async function loadCleaningData(query = {}) {
  const cleaningTasks = await requireItems("/cleaning-tasks", { pageSize: 100, ...query });
  dataStore.cleaningTasks = cleaningTasks;
}

async function loadAuditData() {
  const [operationLogs, operationTypes] = await Promise.all([
    requireItems("/operation-logs", { pageSize: 100 }),
    requireList("/operation-types")
  ]);
  dataStore.operationLogs = operationLogs;
  dataStore.operationTypes = operationTypes;
}

async function requireItems(path, query = {}) {
  const response = await request("GET", path, null, query);
  if (!response || response.code !== 0) throw new Error(response?.message || `接口请求失败：${path}`);
  return responseItems(response);
}

async function safeItems(path, query = {}) {
  const response = await request("GET", path, null, query);
  return response?.code === 0 ? responseItems(response) : [];
}

async function requireList(path, query = {}) {
  const response = await request("GET", path, null, query);
  if (!response || response.code !== 0) throw new Error(response?.message || `接口请求失败：${path}`);
  return responseList(response);
}

async function safeList(path, query = {}) {
  const response = await request("GET", path, null, query);
  return response?.code === 0 ? responseList(response) : [];
}

function responseItems(response) {
  if (Array.isArray(response?.data?.items)) return response.data.items;
  if (Array.isArray(response?.data)) return response.data;
  return [];
}

function responseList(response) {
  if (Array.isArray(response?.data)) return response.data;
  if (Array.isArray(response?.data?.items)) return response.data.items;
  return [];
}

function renderDashboard() {
  const activeOrders = dataStore.checkIns.filter(item => item.orderStatus === "进行中");
  const pendingReservations = dataStore.reservations.filter(item => item.reservationStatus === "未入住");
  const pendingCleaning = dataStore.cleaningTasks.filter(item => item.cleanStatus !== "已完成");
  const revenue = dataStore.checkouts.reduce((sum, item) => sum + Number(item.actualPayAmount), 0);
  return `
    <section class="metrics-grid">
      ${metric("客户总数", dataStore.customers.length, "Customer")}
      ${metric("空闲客房", dataStore.rooms.filter(item => item.roomStatus === "空闲").length, "Room.RoomStatus = 空闲")}
      ${metric("待入住预定", pendingReservations.length, "ReservationStatus = 未入住")}
      ${metric("待处理清扫", pendingCleaning.length, "CleanStatus != 已完成")}
    </section>

    <section class="split-layout">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <h3>房态总览</h3>
            <p>对应接口 ${apiBadge("GET /rooms/status-overview")}</p>
          </div>
        </div>
        <div class="panel-body">${roomBoard()}</div>
      </div>
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <h3>运营统计</h3>
            <p>按规范展示金额和状态枚举</p>
          </div>
        </div>
        <div class="panel-body">
          ${statusChart()}
          <article class="metric-card" style="margin-top: 14px; box-shadow: none;">
            <span>结账实收</span>
            <strong>${money(revenue)}</strong>
            <small>Checkout.ActualPayAmount 汇总</small>
          </article>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>当前在住订单</h3>
          <p>对应接口 ${apiBadge("GET /check-ins")}</p>
        </div>
      </div>
      <div class="panel-body">${checkInsTable(activeOrders, false)}</div>
    </section>
  `;
}

function renderAuth() {
  return `
    <section class="split-layout">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <h3>登录</h3>
            <p>${apiBadge("POST /auth/login")} 成功后保存 JWT Bearer Token</p>
          </div>
        </div>
        <div class="panel-body">
          <form id="loginForm" class="form-grid compact">
            <label class="field"><span>账号名</span><input name="accountName" type="text" value="front01" placeholder="front01" /></label>
            <label class="field"><span>密码</span><input name="password" type="password" value="123456" placeholder="123456" /></label>
            <div class="toolbar">
              <button class="primary-button" type="submit">登录</button>
            </div>
          </form>
          <div class="request-preview" style="margin-top: 14px;">
            <code>Authorization: Bearer &lt;accessToken&gt;</code>
            <code>Content-Type: application/json</code>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <h3>账号注册</h3>
            <p>${apiBadge("POST /accounts/register")} 初始状态为 待审核</p>
          </div>
        </div>
        <div class="panel-body">
          <form id="registerForm" class="form-grid compact">
            ${field("账号名", "accountName", "text", "newstaff01")}
            ${field("密码", "password", "password", "123456")}
            <label class="field"><span>性别</span><select name="sex"><option>男</option><option>女</option></select></label>
            ${field("生日", "birthday", "date", "")}
            ${field("电话", "phone", "text", "13800000000")}
            <label class="field"><span>角色</span><select name="permissionId">${permissionOptions()}</select></label>
            <div class="toolbar"><button class="primary-button" type="submit">提交注册</button></div>
          </form>
        </div>
      </div>
    </section>
  `;
}

function renderAccounts() {
  return `
    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>账号列表</h3>
          <p>${apiBadge("GET /accounts")} ${apiBadge("PATCH /accounts/{accountId}/approval")}</p>
        </div>
        <div class="toolbar">
          <select id="approvalFilter">
            <option value="">全部审批状态</option>
            ${APPROVAL_STATUSES.map(status => `<option value="${status}">${status}</option>`).join("")}
          </select>
        </div>
      </div>
      <div class="panel-body">
        <div id="accountsTable">${accountsTable(dataStore.accounts)}</div>
      </div>
    </section>
  `;
}

function renderCustomers() {
  const showCustomerForm = canManageCustomers();
  return `
    ${showCustomerForm ? `<section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>新增客户</h3>
          <p>${apiBadge("POST /customers")} JSON 字段使用 lowerCamelCase</p>
        </div>
      </div>
      <div class="panel-body">
        <form id="customerForm" class="form-grid">
          ${field("客户姓名", "customerName", "text", "张三")}
          ${field("身份证号", "cardId", "text", "110101199001011234")}
          ${field("客户电话", "customerPhone", "text", "13800000000")}
          <label class="field"><span>折扣等级</span><select name="discountId">${discountOptions()}</select></label>
          <label class="field full"><span>地址</span><input name="address" type="text" placeholder="北京市朝阳区" /></label>
          <div class="toolbar"><button class="primary-button" type="submit">保存客户</button></div>
        </form>
      </div>
    </section>` : ""}

    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>${showCustomerForm ? "客户查询" : "客户查询（只读）"}</h3>
          <p>${apiBadge("GET /customers?cardId=&phone=")}</p>
        </div>
        <div class="toolbar">
          <input id="customerKeyword" type="search" placeholder="姓名 / 身份证 / 电话" />
        </div>
      </div>
      <div class="panel-body">
        <div id="customersTable">${customersTable(dataStore.customers)}</div>
      </div>
    </section>
  `;
}

function renderRooms() {
  const showRoomForms = canManageRooms();
  return `
    ${showRoomForms ? `<section class="split-layout">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <h3>新增客房</h3>
            <p>${apiBadge("POST /rooms")}</p>
          </div>
        </div>
        <div class="panel-body">
          <form id="roomForm" class="form-grid compact">
            ${field("房间号", "roomNo", "text", "401")}
            ${field("楼层", "floorNo", "number", "4")}
            ${field("房间电话", "roomPhone", "text", "8401")}
            <label class="field"><span>房型</span><select name="roomTypeId">${roomTypeOptions()}</select></label>
            <label class="field"><span>房态</span><select name="roomStatus">${ROOM_STATUSES.map(status => `<option>${status}</option>`).join("")}</select></label>
            <div class="toolbar"><button class="primary-button" type="submit">保存客房</button></div>
          </form>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <h3>新增房型</h3>
            <p>${apiBadge("POST /room-types")}</p>
          </div>
        </div>
        <div class="panel-body">
          <form id="roomTypeForm" class="form-grid compact">
            ${field("房型名称", "roomTypeName", "text", "商务房")}
            ${field("房价", "roomPrice", "text", "398.00")}
            <div class="toolbar"><button class="primary-button" type="submit">保存房型</button></div>
          </form>
        </div>
      </div>
    </section>` : ""}

    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>${showRoomForms ? "客房列表" : "客房列表（只读）"}</h3>
          <p>${apiBadge("GET /rooms")} ${apiBadge("GET /rooms/available")}</p>
        </div>
        <div class="toolbar">
          <select id="roomStatusFilter"><option value="">全部房态</option>${ROOM_STATUSES.map(status => `<option>${status}</option>`).join("")}</select>
        </div>
      </div>
      <div class="panel-body">
        <div id="roomsTable">${roomsTable(dataStore.rooms)}</div>
      </div>
    </section>
  `;
}

function renderReservations() {
  return `
    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>创建预定</h3>
          <p>${apiBadge("POST /reservations")} 推荐后端调用 sp_create_reservation</p>
        </div>
      </div>
      <div class="panel-body">
        <form id="reservationForm" class="form-grid">
          <label class="field"><span>客户</span><select name="customerId">${customerOptions()}</select></label>
          <label class="field"><span>房型</span><select name="roomTypeId">${roomTypeOptions()}</select></label>
          ${field("预定入住", "reserveStartTime", "datetime-local", "")}
          ${field("预定离店", "reserveEndTime", "datetime-local", "")}
          ${field("入住人数", "guestCount", "number", "2")}
          ${field("预付款", "prepayAmount", "text", "200.00")}
          <div class="toolbar"><button class="primary-button" type="submit">创建预定</button></div>
        </form>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>预定列表</h3>
          <p>${apiBadge("GET /reservations")} ${apiBadge("PATCH /reservations/{reservationId}/cancel")}</p>
        </div>
        <div class="toolbar">
          <select id="reservationStatusFilter"><option value="">全部预定状态</option>${RESERVATION_STATUSES.map(status => `<option>${status}</option>`).join("")}</select>
        </div>
      </div>
      <div class="panel-body">
        <div id="reservationsTable">${reservationsTable(dataStore.reservations)}</div>
      </div>
    </section>
  `;
}

function renderCheckIns() {
  const active = dataStore.checkIns.filter(item => item.orderStatus === "进行中");
  const showCheckInOps = canManageCheckIns();
  return `
    ${showCheckInOps ? `<section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>直接入住</h3>
          <p>${apiBadge("POST /check-ins")} reservationId 为空表示直接入住</p>
        </div>
      </div>
      <div class="panel-body">
        <form id="checkInForm" class="form-grid">
          <label class="field"><span>客户</span><select name="customerId">${customerOptions()}</select></label>
          <label class="field"><span>空闲房间</span><select name="roomId">${availableRoomOptions()}</select></label>
          ${field("入住时间", "checkInStartTime", "datetime-local", "")}
          ${field("入住人数", "guestCount", "number", "2")}
          ${field("预付款", "prepayAmount", "text", "300.00")}
          <div class="toolbar"><button class="primary-button" type="submit">办理入住</button></div>
        </form>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>在住订单</h3>
          <p>${apiBadge("GET /check-ins")} ${apiBadge("POST /check-ins/{checkInId}/checkout")}</p>
        </div>
      </div>
      <div class="panel-body">${checkInsTable(active, true)}</div>
    </section>` : ""}

    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>${showCheckInOps ? "结账记录" : "结账记录查询"}</h3>
          <p>${apiBadge("GET /checkouts")} 数据源 v_checkout_bill</p>
        </div>
      </div>
      <div class="panel-body">${checkoutsTable(dataStore.checkouts)}</div>
    </section>
  `;
}

function renderCleaning() {
  return `
    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>清扫任务队列</h3>
          <p>${apiBadge("GET /cleaning-tasks")} ${apiBadge("POST /cleaning-tasks/{id}/start")} ${apiBadge("POST /cleaning-tasks/{id}/finish")}</p>
        </div>
        <div class="toolbar">
          <select id="cleanStatusFilter"><option value="">全部清扫状态</option>${CLEAN_STATUSES.map(status => `<option>${status}</option>`).join("")}</select>
        </div>
      </div>
      <div class="panel-body">
        <div id="cleaningTable">${cleaningTable(dataStore.cleaningTasks)}</div>
      </div>
    </section>
  `;
}

function renderAudit() {
  return `
    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>操作审计</h3>
          <p>${apiBadge("GET /operation-logs")} 默认按 operationTime 倒序</p>
        </div>
        <div class="toolbar">
          <input id="logKeyword" type="search" placeholder="操作类型 / 操作者 / 内容" />
        </div>
      </div>
      <div class="panel-body">
        <div id="logsTable">${logsTable(dataStore.operationLogs)}</div>
      </div>
    </section>
  `;
}

function renderFrontendTasks() {
  const tasks = [
    ["遵守接口基准路径", "所有接口从 /api/v1 开始，登录为 POST /auth/login。", "已完成"],
    ["遵守 JSON 字段命名", "前端字段统一使用 lowerCamelCase，例如 customerId、roomStatus。", "已完成"],
    ["统一响应处理", "所有请求按 code、message、data、requestId 处理错误和成功。", "已完成"],
    ["JWT 保存和请求头", "登录后保存 accessToken，后续请求附带 Authorization。", "已完成"],
    ["状态枚举", "房态、预定状态、订单状态、清扫状态和账号状态只使用规范值。", "已完成"],
    ["真实接口联调", "页面数据、表单提交和操作按钮全部请求后端接口。", "已完成"]
  ];
  return `
    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>前端对接任务</h3>
          <p>依据 docs/酒店管理系统对接规范.md 第 10、12、13 节</p>
        </div>
      </div>
      <div class="panel-body">
        <div class="task-list">
          ${tasks.map((task, index) => `
            <article class="task-item">
              <span class="task-index">${index + 1}</span>
              <div><h4>${task[0]}</h4><p>${task[1]}</p></div>
              ${statusPill(task[2])}
            </article>
          `).join("")}
        </div>
      </div>
    </section>
  `;
}

function bindEvents() {
  bindAuth();
  bindAccounts();
  bindCustomers();
  bindRooms();
  bindReservations();
  bindCheckIns();
  bindCleaning();
  bindAudit();
  bindGlobalActions();
}

function bindAuth() {
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = formData(loginForm);
      const response = await request("POST", "/auth/login", payload);
      if (!handleResponse(response, "登录成功")) return;
      accessToken = response.data.accessToken;
      currentAccount = response.data.account;
      localStorage.setItem(TOKEN_KEY, accessToken);
      localStorage.setItem(ACCOUNT_KEY, JSON.stringify(currentAccount));
      activeView = "dashboard";
      render();
    });
  }

  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = formData(registerForm);
      payload.permissionId = Number(payload.permissionId);
      payload.supervisorId = null;
      const response = await request("POST", "/accounts/register", payload);
      if (handleResponse(response, "注册申请已提交")) registerForm.reset();
    });
  }
}

function bindAccounts() {
  const filter = document.getElementById("approvalFilter");
  if (filter) {
    filter.addEventListener("change", async () => {
      await loadAccountsData(filter.value ? { approvalStatus: filter.value } : {});
      document.getElementById("accountsTable").innerHTML = accountsTable(dataStore.accounts);
      bindGlobalActions();
    });
  }
}

function bindCustomers() {
  const form = document.getElementById("customerForm");
  if (form) {
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = formData(form);
      payload.discountId = Number(payload.discountId);
      if (!validateCustomer(payload)) return;
      const response = await request("POST", "/customers", payload);
      if (!handleResponse(response, "客户已保存")) return;
      await refreshCurrentView();
    });
  }

  const keyword = document.getElementById("customerKeyword");
  if (keyword) {
    keyword.addEventListener("input", () => {
      const value = keyword.value.trim();
      const rows = dataStore.customers.filter(item =>
        [item.customerName, item.cardId, item.customerPhone].some(field => String(field || "").includes(value))
      );
      document.getElementById("customersTable").innerHTML = customersTable(rows);
    });
  }
}

function bindRooms() {
  const roomForm = document.getElementById("roomForm");
  if (roomForm) {
    roomForm.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = formData(roomForm);
      payload.floorNo = Number(payload.floorNo);
      payload.roomTypeId = Number(payload.roomTypeId);
      const response = await request("POST", "/rooms", payload);
      if (!handleResponse(response, "客房已保存")) return;
      await refreshCurrentView();
    });
  }

  const roomTypeForm = document.getElementById("roomTypeForm");
  if (roomTypeForm) {
    roomTypeForm.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = formData(roomTypeForm);
      if (!isMoney(payload.roomPrice)) return toast("房型保存失败", "roomPrice 必须是非负金额字符串。", "error");
      const response = await request("POST", "/room-types", payload);
      if (!handleResponse(response, "房型已保存")) return;
      await refreshCurrentView();
    });
  }

  const filter = document.getElementById("roomStatusFilter");
  if (filter) {
    filter.addEventListener("change", async () => {
      await loadRoomsData(filter.value ? { roomStatus: filter.value } : {});
      document.getElementById("roomsTable").innerHTML = roomsTable(dataStore.rooms);
      bindGlobalActions();
    });
  }
}

function bindReservations() {
  const form = document.getElementById("reservationForm");
  if (form) {
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = formData(form);
      payload.customerId = Number(payload.customerId);
      payload.roomTypeId = Number(payload.roomTypeId);
      payload.guestCount = Number(payload.guestCount);
      payload.reserveStartTime = toIso(payload.reserveStartTime);
      payload.reserveEndTime = toIso(payload.reserveEndTime);
      if (!validateBusinessTime(payload.reserveStartTime, payload.reserveEndTime)) return toast("创建预定失败", "reserveStartTime 必须早于 reserveEndTime。", "error");
      if (payload.guestCount <= 0) return toast("创建预定失败", "guestCount 必须为正整数。", "error");
      if (!isMoney(payload.prepayAmount)) return toast("创建预定失败", "prepayAmount 必须是非负金额字符串。", "error");
      const response = await request("POST", "/reservations", payload);
      if (!handleResponse(response, "预定已创建")) return;
      await refreshCurrentView();
    });
  }

  const filter = document.getElementById("reservationStatusFilter");
  if (filter) {
    filter.addEventListener("change", async () => {
      await loadReservationsData(filter.value ? { reservationStatus: filter.value } : {});
      document.getElementById("reservationsTable").innerHTML = reservationsTable(dataStore.reservations);
      bindGlobalActions();
    });
  }
}

function bindCheckIns() {
  const form = document.getElementById("checkInForm");
  if (form) {
    form.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = formData(form);
      payload.customerId = Number(payload.customerId);
      payload.roomId = Number(payload.roomId);
      payload.reservationId = null;
      payload.checkInStartTime = toIso(payload.checkInStartTime);
      payload.checkInEndTime = null;
      payload.guestCount = Number(payload.guestCount);
      if (!payload.roomId) return toast("入住失败", "当前没有可选空闲房间。", "error");
      if (payload.guestCount <= 0) return toast("入住失败", "guestCount 必须为正整数。", "error");
      if (!isMoney(payload.prepayAmount)) return toast("入住失败", "prepayAmount 必须是非负金额字符串。", "error");
      const response = await request("POST", "/check-ins", payload);
      if (!handleResponse(response, "入住办理成功")) return;
      await refreshCurrentView();
    });
  }
}

function bindCleaning() {
  const filter = document.getElementById("cleanStatusFilter");
  if (filter) {
    filter.addEventListener("change", async () => {
      await loadCleaningData(filter.value ? { cleanStatus: filter.value } : {});
      document.getElementById("cleaningTable").innerHTML = cleaningTable(dataStore.cleaningTasks);
      bindGlobalActions();
    });
  }
}

function bindAudit() {
  const keyword = document.getElementById("logKeyword");
  if (keyword) {
    keyword.addEventListener("input", () => {
      const value = keyword.value.trim();
      const rows = dataStore.operationLogs.filter(item =>
        [item.accountName, item.permissionName, item.operationTypeName, item.operationInfo].some(field => String(field || "").includes(value))
      );
      document.getElementById("logsTable").innerHTML = logsTable(rows);
    });
  }
}

function bindGlobalActions() {
  document.querySelectorAll("[data-action]").forEach(button => {
    button.addEventListener("click", async () => {
      const action = button.dataset.action;
      const id = Number(button.dataset.id);
      if (["approve-account", "reject-account", "disable-account"].includes(action) && !canManageAccounts()) return forbidden();
      if (["cancel-reservation", "checkin-reservation"].includes(action) && !canManageReservations()) return forbidden();
      if (action === "checkout" && !canManageCheckIns()) return forbidden();
      if (["start-cleaning", "finish-cleaning"].includes(action) && !canHandleCleaning()) return forbidden();
      if (["set-room-free", "set-room-disabled"].includes(action) && !canManageRooms()) return forbidden();
      if (action === "approve-account") await approveAccount(id, "已启用");
      if (action === "reject-account") await approveAccount(id, "已驳回");
      if (action === "disable-account") await approveAccount(id, "已停用");
      if (action === "cancel-reservation") await cancelReservation(id);
      if (action === "checkin-reservation") await checkInReservation(id);
      if (action === "checkout") await checkout(id);
      if (action === "start-cleaning") await updateCleaning(id, "start");
      if (action === "finish-cleaning") await updateCleaning(id, "finish");
      if (action === "set-room-free") await patchRoomStatus(id, "空闲");
      if (action === "set-room-disabled") await patchRoomStatus(id, "停用");
    });
  });
}

async function approveAccount(accountId, approvalStatus) {
  const response = await request("PATCH", `/accounts/${accountId}/approval`, { approvalStatus, reviewComment: "前端审核" });
  if (!handleResponse(response, "账号状态已更新")) return;
  await refreshCurrentView();
}

async function cancelReservation(reservationId) {
  const response = await request("PATCH", `/reservations/${reservationId}/cancel`, { cancelReason: "前端取消" });
  if (!handleResponse(response, "预定已取消")) return;
  await refreshCurrentView();
}

async function checkInReservation(reservationId) {
  const reservation = dataStore.reservations.find(item => item.reservationId === reservationId);
  if (!reservation) return toast("入住失败", "预定订单不存在。", "error");
  const available = await request("GET", "/rooms/available", null, { roomTypeId: reservation.roomTypeId });
  if (!handleResponse(available, "已查询空闲客房", { silentSuccess: true })) return;
  const rooms = responseItems(available);
  if (!rooms.length) return toast("入住失败", "该房型没有空闲客房。", "error");
  const room = rooms[0];
  const response = await request("POST", "/check-ins", {
    customerId: reservation.customerId,
    roomId: room.roomId,
    reservationId,
    checkInStartTime: reservation.reserveStartTime,
    checkInEndTime: null,
    guestCount: reservation.guestCount,
    prepayAmount: reservation.prepayAmount
  });
  if (!handleResponse(response, "预定已转入住")) return;
  await refreshCurrentView();
}

async function checkout(checkInId) {
  const response = await request("POST", `/check-ins/${checkInId}/checkout`, { checkoutTime: nowIso() });
  if (!handleResponse(response, "结账完成")) return;
  await refreshCurrentView();
}

async function updateCleaning(cleaningTaskId, verb) {
  const response = await request("POST", `/cleaning-tasks/${cleaningTaskId}/${verb}`, { cleanerId: currentAccount?.accountId });
  if (!handleResponse(response, verb === "start" ? "已开始清扫" : "清扫已完成")) return;
  await refreshCurrentView();
}

async function patchRoomStatus(roomId, roomStatus) {
  const response = await request("PATCH", `/rooms/${roomId}`, { roomStatus });
  if (!handleResponse(response, "房态已更新")) return;
  await refreshCurrentView();
}

async function refreshCurrentView() {
  await loadCurrentView(activeView);
}

async function request(method, path, body = null, query = {}) {
  const queryString = new URLSearchParams(removeEmpty(query)).toString();
  const url = `${API_BASE}${path}${queryString ? `?${queryString}` : ""}`;
  try {
    const response = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {})
      },
      body: body ? JSON.stringify(body) : undefined
    });
    const text = await response.text();
    const payload = text ? JSON.parse(text) : { code: response.ok ? 0 : response.status, message: response.statusText, data: null };
    if (payload.code === 40101) {
      logoutWithoutToast();
      render({ load: false });
    }
    return payload;
  } catch (error) {
    return fail(50000, `接口请求失败：${error.message}`);
  }
}

function fail(code, message) {
  return { code, message, data: null, requestId: "" };
}

function handleResponse(response, successMessage, options = {}) {
  if (!response || response.code !== 0) {
    toast("操作失败", response?.message || "未知错误", "error");
    return false;
  }
  if (!options.silentSuccess) toast(successMessage, response.requestId ? `requestId: ${response.requestId}` : "操作已完成");
  return true;
}

function metric(label, value, hint) {
  return `<article class="metric-card"><span>${label}</span><strong>${value}</strong><small>${hint}</small></article>`;
}

function apiBadge(text) {
  return `<span class="api-badge">${escapeHtml(text)}</span>`;
}

function field(label, name, type, placeholder) {
  return `<label class="field"><span>${label}</span><input name="${name}" type="${type}" placeholder="${placeholder}" /></label>`;
}

function accountsTable(rows) {
  if (!rows.length) return empty("没有账号记录");
  return table(
    ["账号ID", "账号名", "角色", "电话", "审批状态", "操作"],
    rows.map(item => [
      `A${item.accountId}`,
      item.accountName,
      item.permissionName || getPermission(item.permissionId).permissionName,
      item.phone || "-",
      statusPill(item.approvalStatus),
      `<div class="row-actions">
        <button class="tiny-button" data-action="approve-account" data-id="${item.accountId}" type="button">启用</button>
        <button class="tiny-button" data-action="reject-account" data-id="${item.accountId}" type="button">驳回</button>
        <button class="tiny-button" data-action="disable-account" data-id="${item.accountId}" type="button">停用</button>
      </div>`
    ])
  );
}

function customersTable(rows) {
  if (!rows.length) return empty("没有客户记录");
  return table(
    ["客户ID", "姓名", "身份证号", "电话", "地址", "折扣"],
    rows.map(item => [
      `C${item.customerId}`,
      item.customerName,
      item.cardId,
      item.customerPhone || "-",
      item.address || "-",
      discountText(item)
    ])
  );
}

function roomsTable(rows) {
  if (!rows.length) return empty("没有客房记录");
  const showActions = canManageRooms();
  return table(
    ["房间ID", "房间号", "楼层", "房型", "电话", "房态", "操作"],
    rows.map(item => [
      `R${item.roomId}`,
      item.roomNo,
      item.floorNo ? `${item.floorNo}F` : "-",
      item.roomTypeName || getRoomType(item.roomTypeId).roomTypeName,
      item.roomPhone || "-",
      statusPill(item.roomStatus),
      showActions ? `<div class="row-actions">
        <button class="tiny-button" data-action="set-room-free" data-id="${item.roomId}" type="button">置空闲</button>
        <button class="tiny-button" data-action="set-room-disabled" data-id="${item.roomId}" type="button">停用</button>
      </div>` : "-"
    ])
  );
}

function reservationsTable(rows) {
  if (!rows.length) return empty("没有预定记录");
  return table(
    ["预定ID", "客户", "房型", "入住时间", "离店时间", "人数", "预付", "状态", "操作"],
    rows.map(item => [
      `B${item.reservationId}`,
      item.customerName || getCustomerName(item.customerId),
      item.roomTypeName || getRoomType(item.roomTypeId).roomTypeName,
      shortTime(item.reserveStartTime),
      shortTime(item.reserveEndTime),
      item.guestCount,
      money(item.prepayAmount),
      statusPill(item.reservationStatus),
      item.reservationStatus === "未入住" && canManageReservations()
        ? `<div class="row-actions">
            <button class="tiny-button" data-action="checkin-reservation" data-id="${item.reservationId}" type="button">转入住</button>
            <button class="tiny-button" data-action="cancel-reservation" data-id="${item.reservationId}" type="button">取消</button>
          </div>`
        : "-"
    ])
  );
}

function checkInsTable(rows, showActions) {
  if (!rows.length) return empty("没有入住订单");
  return table(
    ["入住ID", "客户", "房间", "入住时间", "人数", "预付", "状态", "操作"],
    rows.map(item => [
      `I${item.checkInId}`,
      item.customerName || getCustomerName(item.customerId),
      item.roomNo || getRoomNo(item.roomId),
      shortTime(item.checkInStartTime),
      item.guestCount,
      money(item.prepayAmount),
      statusPill(item.orderStatus),
      showActions && item.orderStatus === "进行中"
        ? `<button class="tiny-button" data-action="checkout" data-id="${item.checkInId}" type="button">结账</button>`
        : "-"
    ])
  );
}

function checkoutsTable(rows) {
  if (!rows.length) return empty("没有结账记录");
  return table(
    ["结账ID", "入住ID", "客户", "房间", "原价", "折后", "预付", "实付/退款", "时间"],
    rows.map(item => [
      `O${item.checkoutId}`,
      `I${item.checkInId}`,
      item.customerName || getCustomerName(item.customerId),
      item.roomNo || getRoomNo(item.roomId),
      money(item.originalAmount),
      money(item.discountAmount),
      money(item.prepayAmount),
      money(item.actualPayAmount),
      shortTime(item.checkoutTime)
    ])
  );
}

function cleaningTable(rows) {
  if (!rows.length) return empty("没有清扫任务");
  const showActions = canHandleCleaning();
  return table(
    ["任务ID", "房间", "保洁员", "截止时间", "完成时间", "状态", "操作"],
    rows.map(item => [
      `K${item.cleaningTaskId}`,
      item.roomNo || getRoomNo(item.roomId),
      item.cleanerName || getAccountName(item.cleanerId),
      shortTime(item.deadlineTime),
      item.finishTime ? shortTime(item.finishTime) : "-",
      statusPill(item.cleanStatus),
      showActions ? `<div class="row-actions">
        ${item.cleanStatus === "待清扫" ? `<button class="tiny-button" data-action="start-cleaning" data-id="${item.cleaningTaskId}" type="button">开始</button>` : ""}
        ${item.cleanStatus === "清扫中" ? `<button class="tiny-button" data-action="finish-cleaning" data-id="${item.cleaningTaskId}" type="button">完成</button>` : ""}
        ${item.cleanStatus === "已完成" ? "-" : ""}
      </div>` : "-"
    ])
  );
}

function logsTable(rows) {
  if (!rows.length) return empty("没有操作日志");
  const sorted = [...rows].sort((a, b) => new Date(b.operationTime) - new Date(a.operationTime));
  return table(
    ["日志ID", "账号", "角色", "类型", "内容", "时间"],
    sorted.map(item => [
      `L${item.operationLogId}`,
      item.accountName,
      item.permissionName,
      item.operationTypeName,
      item.operationInfo,
      shortTime(item.operationTime)
    ])
  );
}

function table(headers, rows) {
  return `
    <div class="table-wrap">
      <table>
        <thead><tr>${headers.map(header => `<th>${escapeHtml(header)}</th>`).join("")}</tr></thead>
        <tbody>
          ${rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function roomBoard() {
  return `<div class="room-board">${dataStore.rooms.map(room => `
    <article class="room-tile ${statusClass(room.roomStatus)}">
      <strong>${escapeHtml(room.roomNo)}</strong>
      <span>${room.floorNo || "-"}F · ${escapeHtml(room.roomTypeName || getRoomType(room.roomTypeId).roomTypeName)}</span>
      ${statusPill(room.roomStatus)}
    </article>
  `).join("") || empty("暂无房态数据")}</div>`;
}

function statusChart() {
  const overview = roomStatusOverview();
  const max = Math.max(1, ...overview.map(item => item.roomCount));
  return `<div class="chart-list">${overview.map(item => `
    <div class="chart-row">
      <span>${item.roomStatus}</span>
      <div class="chart-track"><div class="chart-bar" style="width: ${Math.max(4, item.roomCount / max * 100)}%;"></div></div>
      <strong>${item.roomCount} 间</strong>
    </div>
  `).join("")}</div>`;
}

function roomStatusOverview() {
  if (dataStore.roomOverview.length) {
    return ROOM_STATUSES.map(roomStatus => ({
      roomStatus,
      roomCount: dataStore.roomOverview
        .filter(item => item.roomStatus === roomStatus)
        .reduce((sum, item) => sum + Number(item.roomCount || 0), 0)
    }));
  }
  return ROOM_STATUSES.map(roomStatus => ({
    roomStatus,
    roomCount: dataStore.rooms.filter(item => item.roomStatus === roomStatus).length
  }));
}

function statusPill(status) {
  return `<span class="status-pill ${statusClass(status)}">${escapeHtml(status)}</span>`;
}

function statusClass(status) {
  const map = {
    "空闲": "status-free",
    "已预定": "status-booked",
    "未入住": "status-booked",
    "已入住": "status-occupied",
    "进行中": "status-running",
    "待审核": "status-pending",
    "待清扫": "status-pending",
    "清扫中": "status-cleaning",
    "已完成": "status-success",
    "已启用": "status-enabled",
    "停用": "status-disabled",
    "已停用": "status-disabled",
    "已结束": "status-ended",
    "已取消": "status-cancelled",
    "已驳回": "status-rejected"
  };
  return map[status] || "status-booked";
}

function permissionOptions() {
  const permissions = dataStore.permissions.length ? dataStore.permissions : PUBLIC_PERMISSIONS;
  return permissions.map(item => `<option value="${item.permissionId}">${item.permissionName}</option>`).join("");
}

function discountOptions() {
  if (!dataStore.discounts.length) return `<option value="">请先加载折扣</option>`;
  return dataStore.discounts.map(item => `<option value="${item.discountId}">等级 ${item.discountGrade} · ${percent(item.discountRate)}</option>`).join("");
}

function roomTypeOptions() {
  if (!dataStore.roomTypes.length) return `<option value="">请先加载房型</option>`;
  return dataStore.roomTypes.map(item => `<option value="${item.roomTypeId}">${item.roomTypeName} · ${money(item.roomPrice)}</option>`).join("");
}

function customerOptions() {
  if (!dataStore.customers.length) return `<option value="">请先加载客户</option>`;
  return dataStore.customers.map(item => `<option value="${item.customerId}">${item.customerName} · ${item.cardId}</option>`).join("");
}

function availableRoomOptions() {
  if (!dataStore.availableRooms.length) return `<option value="">暂无空闲房间</option>`;
  return dataStore.availableRooms.map(item => `<option value="${item.roomId}">${item.roomNo} · ${item.roomTypeName || getRoomType(item.roomTypeId).roomTypeName}</option>`).join("");
}

function getPermission(permissionId) {
  const permissions = dataStore.permissions.length ? dataStore.permissions : PUBLIC_PERMISSIONS;
  return permissions.find(item => item.permissionId === Number(permissionId)) || { permissionName: "未知角色" };
}

function getRoomType(roomTypeId) {
  return dataStore.roomTypes.find(item => item.roomTypeId === Number(roomTypeId)) || { roomTypeName: "未知房型", roomPrice: "0.00" };
}

function getCustomerName(customerId) {
  const customer = dataStore.customers.find(item => item.customerId === Number(customerId));
  return customer ? escapeHtml(customer.customerName) : "未知客户";
}

function getRoomNo(roomId) {
  const room = dataStore.rooms.find(item => item.roomId === Number(roomId));
  return room ? escapeHtml(room.roomNo) : "未知房间";
}

function getAccountName(accountId) {
  const account = dataStore.accounts.find(item => item.accountId === Number(accountId));
  return account ? escapeHtml(account.accountName) : "待分配";
}

function discountText(item) {
  if (item.discountGrade !== undefined && item.discountRate !== undefined) return `等级 ${item.discountGrade} · ${percent(item.discountRate)}`;
  const discount = dataStore.discounts.find(row => row.discountId === Number(item.discountId));
  return discount ? `等级 ${discount.discountGrade} · ${percent(discount.discountRate)}` : "-";
}

function validateCustomer(payload) {
  if (!payload.customerName || !payload.cardId) return toast("客户保存失败", "customerName 和 cardId 必填。", "error"), false;
  if (payload.cardId.length !== 18) return toast("客户保存失败", "身份证号建议使用 18 位。", "error"), false;
  if (payload.customerPhone && !/^1\d{10}$/.test(payload.customerPhone)) return toast("客户保存失败", "手机号格式不正确。", "error"), false;
  return true;
}

function validateBusinessTime(startTime, endTime) {
  return startTime && endTime && new Date(startTime) < new Date(endTime);
}

function isMoney(value) {
  return /^\d+(\.\d{1,2})?$/.test(String(value || ""));
}

function money(value) {
  const number = Number(value || 0);
  return number < 0 ? `退款 ${Math.abs(number).toFixed(2)}` : `¥${number.toFixed(2)}`;
}

function percent(value) {
  return `${Math.round(Number(value) * 100)}%`;
}

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function removeEmpty(object) {
  return Object.fromEntries(Object.entries(object || {}).filter(([, value]) => value !== "" && value !== null && value !== undefined));
}

function nowIso() {
  const date = new Date();
  const pad = value => String(value).padStart(2, "0");
  const yyyy = date.getFullYear();
  const mm = pad(date.getMonth() + 1);
  const dd = pad(date.getDate());
  const hh = pad(date.getHours());
  const mi = pad(date.getMinutes());
  const ss = pad(date.getSeconds());
  return `${yyyy}-${mm}-${dd}T${hh}:${mi}:${ss}+08:00`;
}

function toIso(value) {
  if (!value) return "";
  return `${value.length === 16 ? `${value}:00` : value}+08:00`;
}

function shortTime(value) {
  if (!value) return "-";
  return String(value).replace("T", " ").replace("+08:00", "");
}

function empty(text) {
  return `<div class="empty-state">${escapeHtml(text)}</div>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function toast(title, message, type = "success") {
  const stack = document.getElementById("toastStack");
  const node = document.createElement("div");
  node.className = `toast ${type === "error" ? "error" : ""}`;
  node.innerHTML = `<strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span>`;
  stack.appendChild(node);
  setTimeout(() => node.remove(), 2800);
}

document.addEventListener("DOMContentLoaded", init);
