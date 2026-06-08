-- 1. 空闲客房视图
CREATE OR REPLACE VIEW v_available_room AS
SELECT
    r.RoomId,
    r.RoomNo,
    r.FloorNo,
    r.RoomPhone,
    rt.RoomTypeId,
    rt.RoomTypeName,
    rt.RoomPrice,
    r.RoomStatus
FROM Room r
JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
WHERE r.RoomStatus = '空闲';

-- 2. 客房状态总览视图
CREATE OR REPLACE VIEW v_room_status_overview AS
SELECT
    rt.RoomTypeName,
    r.RoomStatus,
    COUNT(*) AS RoomCount
FROM Room r
JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
GROUP BY rt.RoomTypeName, r.RoomStatus;

-- 3. 预定详情视图
CREATE OR REPLACE VIEW v_reservation_detail AS
SELECT
    rv.ReservationId,
    c.CustomerId,
    c.CustomerName,
    c.CustomerPhone,
    rt.RoomTypeName,
    rv.ReserveTime,
    rv.ReserveStartTime,
    rv.ReserveEndTime,
    rv.PrepayAmount,
    rv.GuestCount,
    rv.ReservationStatus,
    ua.AccountName AS OperatorName
FROM Reservation rv
JOIN Customer c ON rv.CustomerId = c.CustomerId
JOIN RoomType rt ON rv.RoomTypeId = rt.RoomTypeId
JOIN UserAccount ua ON rv.OperatorId = ua.AccountId;

-- 4. 入住详情视图
CREATE OR REPLACE VIEW v_checkin_detail AS
SELECT
    ci.CheckInId,
    c.CustomerName,
    c.CardId,
    r.RoomNo,
    rt.RoomTypeName,
    ci.CheckInStartTime,
    ci.CheckInEndTime,
    ci.GuestCount,
    ci.PrepayAmount,
    ci.OrderStatus,
    ci.HandleTime,
    ci.ReservationId,
    ua.AccountName AS OperatorName
FROM CheckIn ci
JOIN Customer c ON ci.CustomerId = c.CustomerId
JOIN Room r ON ci.RoomId = r.RoomId
JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
LEFT JOIN UserAccount ua ON ci.OperatorId = ua.AccountId;

-- 5. 结账账单视图
CREATE OR REPLACE VIEW v_checkout_bill AS
SELECT
    co.CheckoutId,
    co.CheckInId,
    c.CustomerId,          -- 新增
    c.CustomerName,
    c.CardId,
    co.RoomNo,
    co.OriginalAmount,
    co.DiscountRateSnapshot,
    co.DiscountAmount,
    co.PrepayAmount,
    co.ActualPayAmount,
    co.CheckoutTime,
    ua.AccountName AS CashierName,
    co.CashierId           -- 新增
FROM Checkout co
JOIN Customer c ON co.CustomerId = c.CustomerId
JOIN UserAccount ua ON co.CashierId = ua.AccountId;


-- 6. 清扫任务队列视图
CREATE OR REPLACE VIEW v_cleaning_task_queue AS
SELECT
    ct.CleaningTaskId,
    ct.RoomId,
    ct.RoomNo,
    rt.RoomTypeName,
    ct.TaskCreateTime,
    ct.DeadlineTime,
    ct.CleanStatus,
    ct.CleanerId,
    ua.AccountName AS CleanerName,
    ct.FinishTime
FROM CleaningTask ct
JOIN Room r ON ct.RoomId = r.RoomId
JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
LEFT JOIN UserAccount ua ON ct.CleanerId = ua.AccountId;

-- 7. 操作审计视图
CREATE OR REPLACE VIEW v_operation_audit AS
SELECT
    ol.OperationLogId,
    ua.AccountId,
    ua.AccountName,
    ap.PermissionName,
    ot.OperationTypeName,
    ol.OperationInfo,
    ol.OperationTime
FROM OperationLog ol
JOIN UserAccount ua ON ol.OperatorId = ua.AccountId
JOIN AccountPermission ap ON ua.PermissionId = ap.PermissionId
JOIN OperationType ot ON ol.OperationTypeId = ot.OperationTypeId;

CREATE OR REPLACE VIEW v_checkout_bill AS
SELECT
    co.CheckoutId,
    co.CheckInId,
    c.CustomerId,          -- 新增
    c.CustomerName,
    c.CardId,
    co.RoomNo,
    co.OriginalAmount,
    co.DiscountRateSnapshot,
    co.DiscountAmount,
    co.PrepayAmount,
    co.ActualPayAmount,
    co.CheckoutTime,
    ua.AccountName AS CashierName,
    co.CashierId           -- 新增
FROM Checkout co
JOIN Customer c ON co.CustomerId = c.CustomerId
JOIN UserAccount ua ON co.CashierId = ua.AccountId;