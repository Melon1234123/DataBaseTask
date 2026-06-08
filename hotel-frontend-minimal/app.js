const API_BASE = "/api/v1";
const STORE_KEY = "hotelsys_spec_frontend_state_v1";
const TOKEN_KEY = "hotelsys_access_token";
const ACCOUNT_KEY = "hotelsys_current_account";
const REAL_API_KEY = "hotelsys_use_real_api";

const ROOM_STATUSES = ["空闲", "已预定", "已入住", "待清扫", "停用"];
const RESERVATION_STATUSES = ["未入住", "已入住", "已取消"];
const ORDER_STATUSES = ["进行中", "已结束", "已取消"];
const APPROVAL_STATUSES = ["待审核", "已启用", "已驳回", "已停用"];
const CLEAN_STATUSES = ["待清扫", "清扫中", "已完成"];

const navItems = [
  { id: "dashboard", label: "首页总览", code: "D", kicker: "Dashboard", title: "首页总览" },
  { id: "auth", label: "登录注册", code: "A", kicker: "Auth", title: "登录与账号注册" },
  { id: "accounts", label: "账号审核", code: "U", kicker: "Accounts", title: "账号审核与权限" },
  { id: "customers", label: "客户管理", code: "C", kicker: "Customers", title: "客户与折扣管理" },
  { id: "rooms", label: "客房管理", code: "R", kicker: "Rooms", title: "客房类型与客房管理" },
  { id: "reservations", label: "预定管理", code: "B", kicker: "Reservations", title: "客房预定管理" },
  { id: "checkins", label: "入住结账", code: "I", kicker: "Check-ins", title: "入住、换房与结账" },
  { id: "cleaning", label: "清扫任务", code: "K", kicker: "Cleaning", title: "清扫任务管理" },
  { id: "audit", label: "操作审计", code: "L", kicker: "Audit", title: "操作日志查询" },
  { id: "frontendTasks", label: "前端任务", code: "T", kicker: "Tasks", title: "前端对接任务清单" }
];

let activeView = "dashboard";
let useRealApi = localStorage.getItem(REAL_API_KEY) === "true";
let currentAccount = readJson(ACCOUNT_KEY, null);
let accessToken = localStorage.getItem(TOKEN_KEY) || "";
let mockState = loadMockState();

function seedMockState() {
  return {
    permissions: [
      { permissionId: 1, permissionName: "管理员", permissionScope: "账号审核、客房管理、客户管理、预定管理、入住管理、结账管理、操作审计、清扫任务管理" },
      { permissionId: 2, permissionName: "前台工作人员", permissionScope: "客户管理、预定管理、入住管理、结账管理、清扫任务查询" },
      { permissionId: 3, permissionName: "保洁员", permissionScope: "清扫任务查询、清扫开始、清扫完成" },
      { permissionId: 4, permissionName: "审计员", permissionScope: "操作记录查询、账单查询" }
    ],
    accounts: [
      { accountId: 1, accountName: "admin01", password: "123456", sex: "男", birthday: "2000-01-01", phone: "13800000001", permissionId: 1, supervisorId: null, approvalStatus: "已启用" },
      { accountId: 2, accountName: "front01", password: "123456", sex: "女", birthday: "2001-02-02", phone: "13800000002", permissionId: 2, supervisorId: 1, approvalStatus: "已启用" },
      { accountId: 3, accountName: "cleaner01", password: "123456", sex: "女", birthday: "2002-03-03", phone: "13800000003", permissionId: 3, supervisorId: 1, approvalStatus: "待审核" },
      { accountId: 4, accountName: "auditor01", password: "123456", sex: "男", birthday: "2003-04-04", phone: "13800000004", permissionId: 4, supervisorId: 1, approvalStatus: "已启用" }
    ],
    discounts: [
      { discountId: 1, discountGrade: 0, discountRate: "1.0000" },
      { discountId: 2, discountGrade: 1, discountRate: "0.9500" },
      { discountId: 3, discountGrade: 2, discountRate: "0.9000" },
      { discountId: 4, discountGrade: 3, discountRate: "0.8500" }
    ],
    customers: [
      { customerId: 1001, customerName: "张三", cardId: "110101199001011234", customerPhone: "13800010001", address: "北京市朝阳区", discountId: 1 },
      { customerId: 1002, customerName: "李秋", cardId: "330102200202020022", customerPhone: "13800010002", address: "杭州市西湖区", discountId: 2 },
      { customerId: 1003, customerName: "王晨", cardId: "330102200303030033", customerPhone: "13800010003", address: "宁波市鄞州区", discountId: 3 }
    ],
    roomTypes: [
      { roomTypeId: 1, roomTypeName: "标准间", roomPrice: "288.00" },
      { roomTypeId: 2, roomTypeName: "大床房", roomPrice: "328.00" },
      { roomTypeId: 3, roomTypeName: "家庭套房", roomPrice: "568.00" }
    ],
    rooms: [
      { roomId: 2001, roomNo: "101", floorNo: 1, roomPhone: "8101", roomTypeId: 1, roomStatus: "空闲" },
      { roomId: 2002, roomNo: "102", floorNo: 1, roomPhone: "8102", roomTypeId: 1, roomStatus: "已入住" },
      { roomId: 2003, roomNo: "201", floorNo: 2, roomPhone: "8201", roomTypeId: 2, roomStatus: "空闲" },
      { roomId: 2004, roomNo: "202", floorNo: 2, roomPhone: "8202", roomTypeId: 2, roomStatus: "待清扫" },
      { roomId: 2005, roomNo: "301", floorNo: 3, roomPhone: "8301", roomTypeId: 3, roomStatus: "空闲" },
      { roomId: 2006, roomNo: "302", floorNo: 3, roomPhone: "8302", roomTypeId: 3, roomStatus: "停用" }
    ],
    reservations: [
      { reservationId: 3001, customerId: 1001, roomTypeId: 1, reserveTime: "2026-06-08T10:30:00+08:00", reserveStartTime: "2026-06-09T14:00:00+08:00", reserveEndTime: "2026-06-11T12:00:00+08:00", guestCount: 2, prepayAmount: "200.00", reservationStatus: "未入住", operatorId: 2 }
    ],
    checkIns: [
      { checkInId: 4001, customerId: 1003, roomId: 2002, reservationId: null, checkInStartTime: "2026-06-08T14:00:00+08:00", checkInEndTime: null, guestCount: 2, prepayAmount: "300.00", orderStatus: "进行中", operatorId: 2 }
    ],
    checkouts: [],
    cleaningTasks: [
      { cleaningTaskId: 6001, roomId: 2004, cleanStatus: "待清扫", cleanerId: 3, deadlineTime: "2026-06-08T18:00:00+08:00", finishTime: null }
    ],
    operationTypes: [
      { operationTypeId: 1, operationTypeName: "创建预定" },
      { operationTypeId: 2, operationTypeName: "办理入住" },
      { operationTypeId: 3, operationTypeName: "办理结账" },
      { operationTypeId: 4, operationTypeName: "开始清扫" },
      { operationTypeId: 5, operationTypeName: "完成清扫" },
      { operationTypeId: 6, operationTypeName: "账号审核" },
      { operationTypeId: 7, operationTypeName: "客房维护" },
      { operationTypeId: 8, operationTypeName: "客户维护" },
      { operationTypeId: 9, operationTypeName: "换房" }
    ],
    operationLogs: [
      { operationLogId: 1, accountId: 1, accountName: "admin01", permissionName: "管理员", operationTypeName: "系统初始化", operationInfo: "加载规范版前端 Mock 数据", operationTime: "2026-06-08T13:50:00+08:00" }
    ]
  };
}

function loadMockState() {
  return readJson(STORE_KEY, seedMockState());
}

function saveMockState() {
  localStorage.setItem(STORE_KEY, JSON.stringify(mockState));
}

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
  renderNav();
  document.getElementById("toggleApiMode").addEventListener("click", () => {
    useRealApi = !useRealApi;
    localStorage.setItem(REAL_API_KEY, String(useRealApi));
    render();
    toast("接口模式已切换", useRealApi ? "当前将请求真实 /api/v1 后端。" : "当前使用浏览器内置 Mock API。");
  });
  document.getElementById("resetMockData").addEventListener("click", () => {
    mockState = seedMockState();
    saveMockState();
    render();
    toast("Mock 数据已重置", "演示数据恢复到初始状态。");
  });
  render();
}

function renderNav() {
  const nav = document.getElementById("navList");
  nav.innerHTML = navItems.map(item => `
    <button class="nav-button" data-view="${item.id}" type="button">
      <span>${item.label}</span>
    </button>
  `).join("");
  nav.addEventListener("click", event => {
    const button = event.target.closest("[data-view]");
    if (!button) return;
    activeView = button.dataset.view;
    render();
  });
}

function render() {
  const nav = navItems.find(item => item.id === activeView) || navItems[0];
  document.getElementById("pageKicker").textContent = nav.kicker;
  document.getElementById("pageTitle").textContent = nav.title;
  document.getElementById("apiModeLabel").textContent = useRealApi ? "Real API" : "Mock API";
  document.getElementById("apiBaseLabel").textContent = API_BASE;
  document.getElementById("accountChip").textContent = currentAccount
    ? `${currentAccount.accountName} · ${currentAccount.permissionName}`
    : "未登录";
  document.getElementById("toggleApiMode").textContent = useRealApi ? "切换 Mock" : "切换真实接口";

  document.querySelectorAll(".nav-button").forEach(button => {
    button.classList.toggle("active", button.dataset.view === activeView);
  });

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
  bindEvents();
}

function renderDashboard() {
  const activeOrders = mockState.checkIns.filter(item => item.orderStatus === "进行中");
  const pendingReservations = mockState.reservations.filter(item => item.reservationStatus === "未入住");
  const pendingCleaning = mockState.cleaningTasks.filter(item => item.cleanStatus !== "已完成");
  const revenue = mockState.checkouts.reduce((sum, item) => sum + Number(item.actualPayAmount), 0);
  return `
    <section class="metrics-grid">
      ${metric("客户总数", mockState.customers.length, "Customer")}
      ${metric("空闲客房", mockState.rooms.filter(item => item.roomStatus === "空闲").length, "Room.RoomStatus = 空闲")}
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
              <button class="secondary-button" id="logoutButton" type="button">退出登录</button>
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
            <label class="field"><span>上级账号</span><select name="supervisorId">${supervisorOptions()}</select></label>
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
        <div id="accountsTable">${accountsTable(mockState.accounts)}</div>
      </div>
    </section>
  `;
}

function renderCustomers() {
  return `
    <section class="panel">
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
    </section>

    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>客户查询</h3>
          <p>${apiBadge("GET /customers?cardId=&phone=")}</p>
        </div>
        <div class="toolbar">
          <input id="customerKeyword" type="search" placeholder="姓名 / 身份证 / 电话" />
        </div>
      </div>
      <div class="panel-body">
        <div id="customersTable">${customersTable(mockState.customers)}</div>
      </div>
    </section>
  `;
}

function renderRooms() {
  return `
    <section class="split-layout">
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
    </section>

    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>客房列表</h3>
          <p>${apiBadge("GET /rooms")} ${apiBadge("GET /rooms/available")}</p>
        </div>
        <div class="toolbar">
          <select id="roomStatusFilter"><option value="">全部房态</option>${ROOM_STATUSES.map(status => `<option>${status}</option>`).join("")}</select>
        </div>
      </div>
      <div class="panel-body">
        <div id="roomsTable">${roomsTable(mockState.rooms)}</div>
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
        <div id="reservationsTable">${reservationsTable(mockState.reservations)}</div>
      </div>
    </section>
  `;
}

function renderCheckIns() {
  const active = mockState.checkIns.filter(item => item.orderStatus === "进行中");
  return `
    <section class="panel">
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
    </section>

    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <h3>结账记录</h3>
          <p>${apiBadge("GET /checkouts")} 数据源 v_checkout_bill</p>
        </div>
      </div>
      <div class="panel-body">${checkoutsTable(mockState.checkouts)}</div>
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
        <div id="cleaningTable">${cleaningTable(mockState.cleaningTasks)}</div>
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
        <div id="logsTable">${logsTable(mockState.operationLogs)}</div>
      </div>
    </section>
  `;
}

function renderFrontendTasks() {
  const tasks = [
    ["遵守接口基准路径", "所有接口从 /api/v1 开始，登录为 POST /auth/login。", "已完成"],
    ["遵守 JSON 字段命名", "前端字段统一使用 lowerCamelCase，例如 customerId、roomStatus。", "已完成"],
    ["统一响应处理", "所有请求按 code、message、data、requestId 处理错误和成功。", "已完成"],
    ["JWT 保存和请求头", "登录后保存 accessToken，真实接口模式下附带 Authorization。", "已完成"],
    ["状态枚举", "房态、预定状态、订单状态、清扫状态和账号状态只使用规范值。", "已完成"],
    ["Mock API", "后端未完成前用 Mock API 跑通 T05-T13 主流程。", "已完成"],
    ["真实联调", "后端完成后切换真实接口，按第 12 节验收清单逐项测试。", "待联调"]
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
  const logout = document.getElementById("logoutButton");
  if (logout) {
    logout.addEventListener("click", () => {
      accessToken = "";
      currentAccount = null;
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(ACCOUNT_KEY);
      render();
      toast("已退出登录", "本地 token 已清除。");
    });
  }
  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = formData(registerForm);
      payload.permissionId = Number(payload.permissionId);
      payload.supervisorId = payload.supervisorId ? Number(payload.supervisorId) : null;
      const response = await request("POST", "/accounts/register", payload);
      if (handleResponse(response, "注册申请已提交")) render();
    });
  }
}

function bindAccounts() {
  const filter = document.getElementById("approvalFilter");
  if (filter) {
    filter.addEventListener("change", () => {
      const rows = filter.value ? mockState.accounts.filter(item => item.approvalStatus === filter.value) : mockState.accounts;
      document.getElementById("accountsTable").innerHTML = accountsTable(rows);
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
      if (handleResponse(response, "客户已保存")) render();
    });
  }
  const keyword = document.getElementById("customerKeyword");
  if (keyword) {
    keyword.addEventListener("input", () => {
      const value = keyword.value.trim();
      const rows = mockState.customers.filter(item => [item.customerName, item.cardId, item.customerPhone].some(field => String(field).includes(value)));
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
      if (handleResponse(response, "客房已保存")) render();
    });
  }
  const roomTypeForm = document.getElementById("roomTypeForm");
  if (roomTypeForm) {
    roomTypeForm.addEventListener("submit", async event => {
      event.preventDefault();
      const payload = formData(roomTypeForm);
      if (!isMoney(payload.roomPrice)) return toast("房型保存失败", "roomPrice 必须是非负金额字符串。", "error");
      const response = await request("POST", "/room-types", payload);
      if (handleResponse(response, "房型已保存")) render();
    });
  }
  const filter = document.getElementById("roomStatusFilter");
  if (filter) {
    filter.addEventListener("change", () => {
      const rows = filter.value ? mockState.rooms.filter(item => item.roomStatus === filter.value) : mockState.rooms;
      document.getElementById("roomsTable").innerHTML = roomsTable(rows);
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
      if (handleResponse(response, "预定已创建")) render();
    });
  }
  const filter = document.getElementById("reservationStatusFilter");
  if (filter) {
    filter.addEventListener("change", () => {
      const rows = filter.value ? mockState.reservations.filter(item => item.reservationStatus === filter.value) : mockState.reservations;
      document.getElementById("reservationsTable").innerHTML = reservationsTable(rows);
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
      if (handleResponse(response, "入住办理成功")) render();
    });
  }
}

function bindCleaning() {
  const filter = document.getElementById("cleanStatusFilter");
  if (filter) {
    filter.addEventListener("change", () => {
      const rows = filter.value ? mockState.cleaningTasks.filter(item => item.cleanStatus === filter.value) : mockState.cleaningTasks;
      document.getElementById("cleaningTable").innerHTML = cleaningTable(rows);
      bindGlobalActions();
    });
  }
}

function bindAudit() {
  const keyword = document.getElementById("logKeyword");
  if (keyword) {
    keyword.addEventListener("input", () => {
      const value = keyword.value.trim();
      const rows = mockState.operationLogs.filter(item =>
        [item.accountName, item.permissionName, item.operationTypeName, item.operationInfo].some(field => String(field).includes(value))
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
  const response = await request("PATCH", `/accounts/${accountId}/approval`, { approvalStatus, reviewComment: "前端演示审核" });
  if (handleResponse(response, "账号状态已更新")) render();
}

async function cancelReservation(reservationId) {
  const response = await request("PATCH", `/reservations/${reservationId}/cancel`, {});
  if (handleResponse(response, "预定已取消")) render();
}

async function checkInReservation(reservationId) {
  const reservation = mockState.reservations.find(item => item.reservationId === reservationId);
  if (!reservation) return toast("入住失败", "预定订单不存在。", "error");
  const available = await request("GET", "/rooms/available", null, { roomTypeId: reservation.roomTypeId });
  if (!available.data.items.length) return toast("入住失败", "该房型没有空闲客房。", "error");
  const room = available.data.items[0];
  const response = await request("POST", "/check-ins", {
    customerId: reservation.customerId,
    roomId: room.roomId,
    reservationId,
    checkInStartTime: reservation.reserveStartTime,
    checkInEndTime: null,
    guestCount: reservation.guestCount,
    prepayAmount: reservation.prepayAmount
  });
  if (handleResponse(response, "预定已转入住")) render();
}

async function checkout(checkInId) {
  const response = await request("POST", `/check-ins/${checkInId}/checkout`, { checkoutTime: nowIso() });
  if (handleResponse(response, "结账完成")) render();
}

async function updateCleaning(cleaningTaskId, verb) {
  const response = await request("POST", `/cleaning-tasks/${cleaningTaskId}/${verb}`, { cleanerId: currentAccount?.accountId || 3 });
  if (handleResponse(response, verb === "start" ? "已开始清扫" : "清扫已完成")) render();
}

async function patchRoomStatus(roomId, roomStatus) {
  const response = await request("PATCH", `/rooms/${roomId}`, { roomStatus });
  if (handleResponse(response, "房态已更新")) render();
}

async function request(method, path, body = null, query = {}) {
  if (!useRealApi) return mockRequest(method, path, body, query);
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
    return await response.json();
  } catch (error) {
    return fail(50000, `真实接口请求失败：${error.message}`);
  }
}

function mockRequest(method, path, body = null, query = {}) {
  try {
    const cleanPath = path.replace(API_BASE, "");
    if (method === "POST" && cleanPath === "/auth/login") return mockLogin(body);
    if (method === "POST" && cleanPath === "/accounts/register") return mockRegister(body);
    if (method === "GET" && cleanPath === "/accounts") return ok(pageItems(filterAccounts(query)));
    if (method === "GET" && cleanPath === "/permissions") return ok(mockState.permissions);
    if (method === "PATCH" && /^\/accounts\/\d+\/approval$/.test(cleanPath)) return mockAccountApproval(idFrom(cleanPath, 2), body);
    if (method === "GET" && cleanPath === "/discounts") return ok(mockState.discounts);
    if (method === "POST" && cleanPath === "/customers") return mockCreateCustomer(body);
    if (method === "GET" && cleanPath === "/customers") return ok(pageItems(filterCustomers(query)));
    if (method === "PATCH" && /^\/customers\/\d+$/.test(cleanPath)) return mockPatchById("customers", "customerId", idFrom(cleanPath, 2), body, "客户维护");
    if (method === "PATCH" && /^\/customers\/\d+\/discount$/.test(cleanPath)) return mockPatchById("customers", "customerId", idFrom(cleanPath, 2), body, "客户维护");
    if (method === "GET" && cleanPath === "/room-types") return ok(pageItems(mockState.roomTypes));
    if (method === "POST" && cleanPath === "/room-types") return mockCreateRoomType(body);
    if (method === "GET" && cleanPath === "/rooms") return ok(pageItems(filterRooms(query)));
    if (method === "GET" && cleanPath === "/rooms/available") return ok(pageItems(availableRooms(query.roomTypeId)));
    if (method === "GET" && cleanPath === "/rooms/status-overview") return ok(roomStatusOverview());
    if (method === "POST" && cleanPath === "/rooms") return mockCreateRoom(body);
    if (method === "PATCH" && /^\/rooms\/\d+$/.test(cleanPath)) return mockPatchById("rooms", "roomId", idFrom(cleanPath, 2), body, "客房维护");
    if (method === "POST" && cleanPath === "/reservations") return mockCreateReservation(body);
    if (method === "GET" && cleanPath === "/reservations") return ok(pageItems(filterReservations(query)));
    if (method === "PATCH" && /^\/reservations\/\d+\/cancel$/.test(cleanPath)) return mockCancelReservation(idFrom(cleanPath, 2));
    if (method === "POST" && cleanPath === "/check-ins") return mockCreateCheckIn(body);
    if (method === "GET" && cleanPath === "/check-ins") return ok(pageItems(filterCheckIns(query)));
    if (method === "POST" && /^\/check-ins\/\d+\/checkout$/.test(cleanPath)) return mockCheckout(idFrom(cleanPath, 2), body);
    if (method === "GET" && cleanPath === "/checkouts") return ok(pageItems(mockState.checkouts));
    if (method === "GET" && cleanPath === "/cleaning-tasks") return ok(pageItems(filterCleaningTasks(query)));
    if (method === "POST" && /^\/cleaning-tasks\/\d+\/start$/.test(cleanPath)) return mockCleaning(idFrom(cleanPath, 2), "清扫中", "开始清扫");
    if (method === "POST" && /^\/cleaning-tasks\/\d+\/finish$/.test(cleanPath)) return mockCleaning(idFrom(cleanPath, 2), "已完成", "完成清扫");
    if (method === "GET" && cleanPath === "/operation-types") return ok(mockState.operationTypes);
    if (method === "GET" && cleanPath === "/operation-logs") return ok(pageItems(filterLogs(query)));
    return fail(40401, `Mock API 未实现 ${method} ${cleanPath}`);
  } catch (error) {
    return fail(50000, error.message);
  }
}

function mockLogin(body) {
  const account = mockState.accounts.find(item => item.accountName === body.accountName);
  if (!account || account.password !== body.password) return fail(40101, "账号不存在或密码错误");
  if (account.approvalStatus !== "已启用") return fail(40301, "账号未启用，不能登录");
  const permission = getPermission(account.permissionId);
  return ok({
    accessToken: `mock-token-${account.accountId}-${Date.now()}`,
    tokenType: "Bearer",
    expiresIn: 7200,
    account: {
      accountId: account.accountId,
      accountName: account.accountName,
      permissionName: permission.permissionName,
      approvalStatus: account.approvalStatus
    }
  });
}

function mockRegister(body) {
  if (mockState.accounts.some(item => item.accountName === body.accountName)) return fail(40902, "账号名已存在");
  const account = {
    accountId: nextId(mockState.accounts, "accountId"),
    accountName: body.accountName,
    password: body.password,
    sex: body.sex,
    birthday: body.birthday,
    phone: body.phone,
    permissionId: Number(body.permissionId),
    supervisorId: body.supervisorId ? Number(body.supervisorId) : null,
    approvalStatus: "待审核"
  };
  mockState.accounts.push(account);
  addLog("账号审核", `账号 ${account.accountName} 提交注册申请`);
  saveMockState();
  return ok({ accountId: account.accountId, approvalStatus: account.approvalStatus });
}

function mockAccountApproval(accountId, body) {
  const account = mockState.accounts.find(item => item.accountId === accountId);
  if (!account) return fail(40401, "账号不存在");
  if (!["已启用", "已驳回", "已停用"].includes(body.approvalStatus)) return fail(40002, "审批状态非法");
  account.approvalStatus = body.approvalStatus;
  addLog("账号审核", `账号 ${account.accountName} 审批状态改为 ${body.approvalStatus}`);
  saveMockState();
  return ok({ accountId, approvalStatus: account.approvalStatus });
}

function mockCreateCustomer(body) {
  if (mockState.customers.some(item => item.cardId === body.cardId)) return fail(40902, "身份证号已存在");
  if (!mockState.discounts.some(item => item.discountId === Number(body.discountId))) return fail(40002, "discountId 不存在");
  const customer = {
    customerId: nextId(mockState.customers, "customerId"),
    customerName: body.customerName,
    cardId: body.cardId,
    customerPhone: body.customerPhone,
    address: body.address || "",
    discountId: Number(body.discountId)
  };
  mockState.customers.push(customer);
  addLog("客户维护", `新增客户 ${customer.customerName}`);
  saveMockState();
  return ok(customer);
}

function mockCreateRoomType(body) {
  if (mockState.roomTypes.some(item => item.roomTypeName === body.roomTypeName)) return fail(40902, "房型名称已存在");
  const roomType = {
    roomTypeId: nextId(mockState.roomTypes, "roomTypeId"),
    roomTypeName: body.roomTypeName,
    roomPrice: normalizeMoney(body.roomPrice)
  };
  mockState.roomTypes.push(roomType);
  addLog("客房维护", `新增房型 ${roomType.roomTypeName}`);
  saveMockState();
  return ok(roomType);
}

function mockCreateRoom(body) {
  if (mockState.rooms.some(item => item.roomNo === body.roomNo)) return fail(40902, "房间号已存在");
  if (!ROOM_STATUSES.includes(body.roomStatus)) return fail(40002, "roomStatus 非法");
  const room = {
    roomId: nextId(mockState.rooms, "roomId"),
    roomNo: body.roomNo,
    floorNo: Number(body.floorNo),
    roomPhone: body.roomPhone || "",
    roomTypeId: Number(body.roomTypeId),
    roomStatus: body.roomStatus || "空闲"
  };
  mockState.rooms.push(room);
  addLog("客房维护", `新增客房 ${room.roomNo}`);
  saveMockState();
  return ok(room);
}

function mockCreateReservation(body) {
  if (!mockState.customers.some(item => item.customerId === Number(body.customerId))) return fail(40401, "客户不存在");
  if (!mockState.roomTypes.some(item => item.roomTypeId === Number(body.roomTypeId))) return fail(40401, "房型不存在");
  if (!validateBusinessTime(body.reserveStartTime, body.reserveEndTime)) return fail(40002, "预定时间非法");
  if (Number(body.guestCount) <= 0) return fail(40002, "入住人数必须为正整数");
  if (!isMoney(body.prepayAmount)) return fail(40002, "预付款金额非法");
  if (!availableRooms(body.roomTypeId).length) return fail(40901, "当前房型没有空闲客房");
  const reservation = {
    reservationId: nextId(mockState.reservations, "reservationId"),
    customerId: Number(body.customerId),
    roomTypeId: Number(body.roomTypeId),
    reserveTime: nowIso(),
    reserveStartTime: body.reserveStartTime,
    reserveEndTime: body.reserveEndTime,
    guestCount: Number(body.guestCount),
    prepayAmount: normalizeMoney(body.prepayAmount),
    reservationStatus: "未入住",
    operatorId: currentAccount?.accountId || 2
  };
  mockState.reservations.push(reservation);
  addLog("创建预定", `创建预定 ${reservation.reservationId}，客户 ${getCustomerName(reservation.customerId)}`);
  saveMockState();
  return ok({ reservationId: reservation.reservationId, reservationStatus: reservation.reservationStatus });
}

function mockCancelReservation(reservationId) {
  const reservation = mockState.reservations.find(item => item.reservationId === reservationId);
  if (!reservation) return fail(40401, "预定订单不存在");
  if (reservation.reservationStatus !== "未入住") return fail(40901, "只有未入住预定可以取消");
  reservation.reservationStatus = "已取消";
  addLog("创建预定", `取消预定 ${reservationId}`);
  saveMockState();
  return ok({ reservationId, reservationStatus: reservation.reservationStatus });
}

function mockCreateCheckIn(body) {
  const room = mockState.rooms.find(item => item.roomId === Number(body.roomId));
  if (!room) return fail(40401, "房间不存在");
  if (room.roomStatus !== "空闲") return fail(40901, "客房当前不是空闲状态，不能办理入住");
  if (!mockState.customers.some(item => item.customerId === Number(body.customerId))) return fail(40401, "客户不存在");
  if (body.reservationId) {
    const reservation = mockState.reservations.find(item => item.reservationId === Number(body.reservationId));
    if (!reservation) return fail(40401, "预定不存在");
    if (reservation.reservationStatus !== "未入住") return fail(40901, "预定不是未入住状态");
    reservation.reservationStatus = "已入住";
  }
  const checkIn = {
    checkInId: nextId(mockState.checkIns, "checkInId"),
    customerId: Number(body.customerId),
    roomId: Number(body.roomId),
    reservationId: body.reservationId ? Number(body.reservationId) : null,
    checkInStartTime: body.checkInStartTime,
    checkInEndTime: body.checkInEndTime || null,
    guestCount: Number(body.guestCount),
    prepayAmount: normalizeMoney(body.prepayAmount),
    orderStatus: "进行中",
    operatorId: currentAccount?.accountId || 2
  };
  mockState.checkIns.push(checkIn);
  room.roomStatus = "已入住";
  addLog("办理入住", `入住订单 ${checkIn.checkInId}，房间 ${room.roomNo}`);
  saveMockState();
  return ok({ checkInId: checkIn.checkInId, orderStatus: checkIn.orderStatus });
}

function mockCheckout(checkInId, body) {
  const checkIn = mockState.checkIns.find(item => item.checkInId === checkInId);
  if (!checkIn) return fail(40401, "入住订单不存在");
  if (checkIn.orderStatus !== "进行中") return fail(40901, "只有进行中订单可以结账");
  const room = mockState.rooms.find(item => item.roomId === checkIn.roomId);
  const roomType = getRoomType(room.roomTypeId);
  const customer = mockState.customers.find(item => item.customerId === checkIn.customerId);
  const discount = mockState.discounts.find(item => item.discountId === customer.discountId) || mockState.discounts[0];
  const checkoutTime = body.checkoutTime || nowIso();
  const days = Math.max(1, Math.ceil((new Date(checkoutTime) - new Date(checkIn.checkInStartTime)) / 86400000));
  const originalAmount = Number(roomType.roomPrice) * days;
  const discountAmount = originalAmount * Number(discount.discountRate);
  const actualPayAmount = discountAmount - Number(checkIn.prepayAmount);
  checkIn.orderStatus = "已结束";
  checkIn.checkInEndTime = checkoutTime;
  room.roomStatus = "待清扫";
  const checkout = {
    checkoutId: nextId(mockState.checkouts, "checkoutId", 5000),
    checkInId,
    customerId: checkIn.customerId,
    roomId: room.roomId,
    cashierId: currentAccount?.accountId || 2,
    originalAmount: normalizeMoney(originalAmount),
    discountRateSnapshot: discount.discountRate,
    discountAmount: normalizeMoney(discountAmount),
    prepayAmount: checkIn.prepayAmount,
    actualPayAmount: normalizeMoney(actualPayAmount),
    checkoutTime
  };
  mockState.checkouts.push(checkout);
  mockState.cleaningTasks.push({
    cleaningTaskId: nextId(mockState.cleaningTasks, "cleaningTaskId", 6000),
    roomId: room.roomId,
    cleanStatus: "待清扫",
    cleanerId: 3,
    deadlineTime: checkoutTime,
    finishTime: null
  });
  addLog("办理结账", `办理结账记录 ${checkout.checkoutId}，入住订单ID ${checkInId}`);
  saveMockState();
  return ok(checkout);
}

function mockCleaning(cleaningTaskId, targetStatus, operationTypeName) {
  const task = mockState.cleaningTasks.find(item => item.cleaningTaskId === cleaningTaskId);
  if (!task) return fail(40401, "清扫任务不存在");
  if (targetStatus === "清扫中" && task.cleanStatus !== "待清扫") return fail(40901, "只有待清扫任务可以开始");
  if (targetStatus === "已完成" && task.cleanStatus !== "清扫中") return fail(40901, "只有清扫中任务可以完成");
  task.cleanStatus = targetStatus;
  if (targetStatus === "已完成") {
    task.finishTime = nowIso();
    const room = mockState.rooms.find(item => item.roomId === task.roomId);
    if (room) room.roomStatus = "空闲";
  }
  addLog(operationTypeName, `${operationTypeName}任务 ${cleaningTaskId}，房间 ${getRoomNo(task.roomId)}`);
  saveMockState();
  return ok({ cleaningTaskId, cleanStatus: task.cleanStatus });
}

function mockPatchById(listName, idName, id, body, operationTypeName) {
  const item = mockState[listName].find(row => row[idName] === id);
  if (!item) return fail(40401, "资源不存在");
  Object.assign(item, body);
  addLog(operationTypeName, `修改资源 ${id}`);
  saveMockState();
  return ok(item);
}

function filterAccounts(query) {
  return mockState.accounts.filter(item => !query.approvalStatus || item.approvalStatus === query.approvalStatus);
}

function filterCustomers(query) {
  return mockState.customers.filter(item =>
    (!query.cardId || item.cardId.includes(query.cardId)) &&
    (!query.phone || item.customerPhone.includes(query.phone)) &&
    (!query.customerName || item.customerName.includes(query.customerName))
  );
}

function filterRooms(query) {
  return mockState.rooms.filter(item =>
    (!query.roomStatus || item.roomStatus === query.roomStatus) &&
    (!query.roomTypeId || item.roomTypeId === Number(query.roomTypeId))
  );
}

function filterReservations(query) {
  return mockState.reservations.filter(item =>
    (!query.customerId || item.customerId === Number(query.customerId)) &&
    (!query.reservationStatus || item.reservationStatus === query.reservationStatus) &&
    (!query.roomTypeId || item.roomTypeId === Number(query.roomTypeId))
  );
}

function filterCheckIns(query) {
  return mockState.checkIns.filter(item => !query.orderStatus || item.orderStatus === query.orderStatus);
}

function filterCleaningTasks(query) {
  return mockState.cleaningTasks.filter(item => !query.cleanStatus || item.cleanStatus === query.cleanStatus);
}

function filterLogs(query) {
  return [...mockState.operationLogs]
    .sort((a, b) => new Date(b.operationTime) - new Date(a.operationTime))
    .filter(item => !query.operationTypeName || item.operationTypeName === query.operationTypeName);
}

function availableRooms(roomTypeId) {
  return mockState.rooms.filter(item => item.roomStatus === "空闲" && (!roomTypeId || item.roomTypeId === Number(roomTypeId)));
}

function roomStatusOverview() {
  return ROOM_STATUSES.map(roomStatus => ({
    roomStatus,
    roomCount: mockState.rooms.filter(item => item.roomStatus === roomStatus).length
  }));
}

function ok(data) {
  return { code: 0, message: "success", data, requestId: requestId() };
}

function fail(code, message) {
  return { code, message, data: null, requestId: requestId() };
}

function requestId() {
  return `req-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
}

function pageItems(items, page = 1, pageSize = 20) {
  return { items, total: items.length, page, pageSize };
}

function handleResponse(response, successMessage) {
  if (!response || response.code !== 0) {
    toast("操作失败", response?.message || "未知错误", "error");
    return false;
  }
  toast(successMessage, `requestId: ${response.requestId}`);
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
    rows.map(item => {
      const permission = getPermission(item.permissionId);
      return [
        `A${item.accountId}`,
        item.accountName,
        permission.permissionName,
        item.phone,
        statusPill(item.approvalStatus),
        `<div class="row-actions">
          <button class="tiny-button" data-action="approve-account" data-id="${item.accountId}" type="button">启用</button>
          <button class="tiny-button" data-action="reject-account" data-id="${item.accountId}" type="button">驳回</button>
          <button class="tiny-button" data-action="disable-account" data-id="${item.accountId}" type="button">停用</button>
        </div>`
      ];
    })
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
      item.customerPhone,
      item.address || "-",
      discountText(item.discountId)
    ])
  );
}

function roomsTable(rows) {
  if (!rows.length) return empty("没有客房记录");
  return table(
    ["房间ID", "房间号", "楼层", "房型", "电话", "房态", "操作"],
    rows.map(item => [
      `R${item.roomId}`,
      item.roomNo,
      `${item.floorNo}F`,
      getRoomType(item.roomTypeId).roomTypeName,
      item.roomPhone || "-",
      statusPill(item.roomStatus),
      `<div class="row-actions">
        <button class="tiny-button" data-action="set-room-free" data-id="${item.roomId}" type="button">置空闲</button>
        <button class="tiny-button" data-action="set-room-disabled" data-id="${item.roomId}" type="button">停用</button>
      </div>`
    ])
  );
}

function reservationsTable(rows) {
  if (!rows.length) return empty("没有预定记录");
  return table(
    ["预定ID", "客户", "房型", "入住时间", "离店时间", "人数", "预付", "状态", "操作"],
    rows.map(item => [
      `B${item.reservationId}`,
      getCustomerName(item.customerId),
      getRoomType(item.roomTypeId).roomTypeName,
      shortTime(item.reserveStartTime),
      shortTime(item.reserveEndTime),
      item.guestCount,
      money(item.prepayAmount),
      statusPill(item.reservationStatus),
      item.reservationStatus === "未入住"
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
      getCustomerName(item.customerId),
      getRoomNo(item.roomId),
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
      getCustomerName(item.customerId),
      getRoomNo(item.roomId),
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
  return table(
    ["任务ID", "房间", "保洁员", "截止时间", "完成时间", "状态", "操作"],
    rows.map(item => [
      `K${item.cleaningTaskId}`,
      getRoomNo(item.roomId),
      getAccountName(item.cleanerId),
      shortTime(item.deadlineTime),
      item.finishTime ? shortTime(item.finishTime) : "-",
      statusPill(item.cleanStatus),
      `<div class="row-actions">
        ${item.cleanStatus === "待清扫" ? `<button class="tiny-button" data-action="start-cleaning" data-id="${item.cleaningTaskId}" type="button">开始</button>` : ""}
        ${item.cleanStatus === "清扫中" ? `<button class="tiny-button" data-action="finish-cleaning" data-id="${item.cleaningTaskId}" type="button">完成</button>` : ""}
        ${item.cleanStatus === "已完成" ? "-" : ""}
      </div>`
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
  return `<div class="room-board">${mockState.rooms.map(room => `
    <article class="room-tile ${statusClass(room.roomStatus)}">
      <strong>${escapeHtml(room.roomNo)}</strong>
      <span>${room.floorNo}F · ${escapeHtml(getRoomType(room.roomTypeId).roomTypeName)}</span>
      ${statusPill(room.roomStatus)}
    </article>
  `).join("")}</div>`;
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
    "已驳回": "status-rejected",
    "已完成": "status-success",
    "已完成原型": "status-success",
    "已完成": "status-success",
    "待联调": "status-pending"
  };
  return map[status] || "status-booked";
}

function permissionOptions() {
  return mockState.permissions.map(item => `<option value="${item.permissionId}">${item.permissionName}</option>`).join("");
}

function supervisorOptions() {
  return `<option value="">无</option>${mockState.accounts.filter(item => item.approvalStatus === "已启用").map(item => `<option value="${item.accountId}">${item.accountName}</option>`).join("")}`;
}

function discountOptions() {
  return mockState.discounts.map(item => `<option value="${item.discountId}">等级 ${item.discountGrade} · ${percent(item.discountRate)}</option>`).join("");
}

function roomTypeOptions() {
  return mockState.roomTypes.map(item => `<option value="${item.roomTypeId}">${item.roomTypeName} · ${money(item.roomPrice)}</option>`).join("");
}

function customerOptions() {
  return mockState.customers.map(item => `<option value="${item.customerId}">${item.customerName} · ${item.cardId}</option>`).join("");
}

function availableRoomOptions() {
  const rooms = availableRooms();
  if (!rooms.length) return `<option value="">暂无空闲房间</option>`;
  return rooms.map(item => `<option value="${item.roomId}">${item.roomNo} · ${getRoomType(item.roomTypeId).roomTypeName}</option>`).join("");
}

function getPermission(permissionId) {
  return mockState.permissions.find(item => item.permissionId === Number(permissionId)) || { permissionName: "未知角色" };
}

function getRoomType(roomTypeId) {
  return mockState.roomTypes.find(item => item.roomTypeId === Number(roomTypeId)) || { roomTypeName: "未知房型", roomPrice: "0.00" };
}

function getCustomerName(customerId) {
  const customer = mockState.customers.find(item => item.customerId === Number(customerId));
  return customer ? escapeHtml(customer.customerName) : "未知客户";
}

function getRoomNo(roomId) {
  const room = mockState.rooms.find(item => item.roomId === Number(roomId));
  return room ? escapeHtml(room.roomNo) : "未知房间";
}

function getAccountName(accountId) {
  const account = mockState.accounts.find(item => item.accountId === Number(accountId));
  return account ? escapeHtml(account.accountName) : "待分配";
}

function discountText(discountId) {
  const discount = mockState.discounts.find(item => item.discountId === Number(discountId));
  return discount ? `等级 ${discount.discountGrade} · ${percent(discount.discountRate)}` : "-";
}

function addLog(operationTypeName, operationInfo) {
  const account = currentAccount || { accountId: 1, accountName: "admin01", permissionName: "管理员" };
  mockState.operationLogs.push({
    operationLogId: nextId(mockState.operationLogs, "operationLogId"),
    accountId: account.accountId,
    accountName: account.accountName,
    permissionName: account.permissionName,
    operationTypeName,
    operationInfo,
    operationTime: nowIso()
  });
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

function normalizeMoney(value) {
  return Number(value || 0).toFixed(2);
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

function nextId(list, key, base = 0) {
  return list.length ? Math.max(...list.map(item => Number(item[key]) || 0)) + 1 : base + 1;
}

function idFrom(path, index) {
  return Number(path.split("/")[index]);
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
