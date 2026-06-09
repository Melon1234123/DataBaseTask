-- ======================================================
-- 存储过程文件 Procedures.sql
-- 包含所有业务存储过程，支持事务回滚和错误处理
-- ======================================================

DELIMITER $$

-- 1. 写入操作日志（无事务，不需要异常处理器）
CREATE PROCEDURE sp_add_operation_log(
    IN p_operator_id INT,
    IN p_operation_type_name VARCHAR(50),
    IN p_operation_info VARCHAR(1024)
)
BEGIN
    DECLARE v_operation_type_id INT DEFAULT NULL;

    SELECT OperationTypeId
    INTO v_operation_type_id
    FROM OperationType
    WHERE OperationTypeName = p_operation_type_name;

    IF v_operation_type_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '操作类型不存在，不能写入操作日志';
    END IF;

    INSERT INTO OperationLog(OperatorId, OperationTypeId, OperationInfo, OperationTime)
    VALUES(p_operator_id, v_operation_type_id, p_operation_info, NOW());
END$$

-- 2. 创建预定
CREATE PROCEDURE sp_create_reservation(
    IN p_customer_id INT,
    IN p_room_type_id INT,
    IN p_operator_id INT,
    IN p_start_time DATETIME,
    IN p_end_time DATETIME,
    IN p_guest_count INT,
    IN p_prepay DECIMAL(10,2),
    OUT p_reservation_id INT
)
BEGIN
    DECLARE v_operator_status VARCHAR(20);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SELECT ApprovalStatus
    INTO v_operator_status
    FROM UserAccount
    WHERE AccountId = p_operator_id;

    IF v_operator_status <> '已启用' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '操作员账号未启用，不能创建预定';
    END IF;

    IF p_start_time >= p_end_time THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '预定开始时间必须早于预定结束时间';
    END IF;

    IF p_guest_count <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '入住人数必须大于0';
    END IF;

    IF p_prepay < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '预支付金额不能为负';
    END IF;

    START TRANSACTION;

    INSERT INTO Reservation(
        ReserveTime, ReserveStartTime, ReserveEndTime, PrepayAmount,
        GuestCount, RoomTypeId, CustomerId, OperatorId, ReservationStatus
    ) VALUES (
        NOW(), p_start_time, p_end_time, p_prepay,
        p_guest_count, p_room_type_id, p_customer_id, p_operator_id, '未入住'
    );

    SET p_reservation_id = LAST_INSERT_ID();

    CALL sp_add_operation_log(
        p_operator_id,
        '创建预定',
        CONCAT('创建预定订单 ', p_reservation_id, '，客户ID ', p_customer_id)
    );

    COMMIT;
END$$

-- 3. 办理入住（增强版：校验预定状态、客户匹配、房型匹配）
CREATE PROCEDURE sp_check_in(
    IN p_customer_id INT,
    IN p_room_id INT,
    IN p_reservation_id INT,
    IN p_operator_id INT,
    IN p_start_time DATETIME,
    IN p_end_time DATETIME,
    IN p_guest_count INT,
    IN p_prepay DECIMAL(10,2),
    OUT p_checkin_id INT
)
BEGIN
    DECLARE v_room_status VARCHAR(20);
    DECLARE v_operator_status VARCHAR(20);
    DECLARE v_reserve_status VARCHAR(20);
    DECLARE v_reserve_customer_id INT;
    DECLARE v_reserve_room_type_id INT;
    DECLARE v_room_room_type_id INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 1. 锁定并校验房间状态
    SELECT RoomStatus, RoomTypeId
    INTO v_room_status, v_room_room_type_id
    FROM Room
    WHERE RoomId = p_room_id
    FOR UPDATE;

    SELECT ApprovalStatus
    INTO v_operator_status
    FROM UserAccount
    WHERE AccountId = p_operator_id;

    IF v_operator_status <> '已启用' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '操作员账号未启用，不能办理入住';
    END IF;

    IF v_room_status <> '空闲' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '客房当前不是空闲状态，不能办理入住';
    END IF;

    IF p_guest_count <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '入住人数必须大于0';
    END IF;

    IF p_prepay < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '预支付金额不能为负';
    END IF;

    -- 2. 如果有关联预定，进行校验
    IF p_reservation_id IS NOT NULL THEN
        SELECT ReservationStatus, CustomerId, RoomTypeId
        INTO v_reserve_status, v_reserve_customer_id, v_reserve_room_type_id
        FROM Reservation
        WHERE ReservationId = p_reservation_id
        FOR UPDATE;

        IF v_reserve_status <> '未入住' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '预定订单状态不是未入住，不能用于办理入住';
        END IF;

        IF v_reserve_customer_id <> p_customer_id THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '预定订单的客户与当前客户不一致';
        END IF;

        IF v_room_room_type_id <> v_reserve_room_type_id THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '预定房型与所选房间的房型不匹配';
        END IF;
    END IF;

    -- 3. 创建入住记录
    INSERT INTO CheckIn(
        CheckInStartTime, CheckInEndTime, GuestCount, PrepayAmount,
        OrderStatus, HandleTime, CustomerId, RoomId, ReservationId, OperatorId
    ) VALUES (
        p_start_time, p_end_time, p_guest_count, p_prepay,
        '进行中', NOW(), p_customer_id, p_room_id, p_reservation_id, p_operator_id
    );

    SET p_checkin_id = LAST_INSERT_ID();

    CALL sp_add_operation_log(
        p_operator_id,
        '办理入住',
        CONCAT('办理入住订单 ', p_checkin_id, '，客户ID ', p_customer_id, '，客房ID ', p_room_id)
    );

    COMMIT;
END$$

-- 4. 办理结账（支持传入结账时间）
CREATE PROCEDURE sp_checkout(
    IN p_checkin_id INT,
    IN p_cashier_id INT,
    IN p_checkout_time DATETIME,
    OUT p_checkout_id INT
)
BEGIN
    DECLARE v_customer_id INT DEFAULT NULL;
    DECLARE v_room_id INT;
    DECLARE v_room_no VARCHAR(30);
    DECLARE v_room_price DECIMAL(10,2);
    DECLARE v_discount_rate DECIMAL(5,4);
    DECLARE v_prepay DECIMAL(10,2);
    DECLARE v_start DATETIME;
    DECLARE v_end DATETIME;
    DECLARE v_days INT;
    DECLARE v_original DECIMAL(10,2);
    DECLARE v_discount_amount DECIMAL(10,2);
    DECLARE v_actual DECIMAL(10,2);
    DECLARE v_not_found TINYINT DEFAULT 0;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_not_found = 1;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT
        ci.CustomerId,
        ci.RoomId,
        r.RoomNo,
        rt.RoomPrice,
        d.DiscountRate,
        ci.PrepayAmount,
        ci.CheckInStartTime,
        COALESCE(ci.CheckInEndTime, p_checkout_time)
    INTO
        v_customer_id,
        v_room_id,
        v_room_no,
        v_room_price,
        v_discount_rate,
        v_prepay,
        v_start,
        v_end
    FROM CheckIn ci
    JOIN Room r ON ci.RoomId = r.RoomId
    JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
    JOIN Customer c ON ci.CustomerId = c.CustomerId
    JOIN Discount d ON c.DiscountId = d.DiscountId
    WHERE ci.CheckInId = p_checkin_id
      AND ci.OrderStatus = '进行中'
    FOR UPDATE;

    IF v_not_found = 1 OR v_customer_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '入住订单不存在或已结账';
    END IF;

    -- 校验结账时间不能早于入住开始时间
    IF v_start > p_checkout_time THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '结账时间不能早于入住开始时间';
    END IF;
    IF v_start = p_checkout_time THEN
        SET p_checkout_time = DATE_ADD(v_start, INTERVAL 1 SECOND);
    END IF;

    SET v_days = GREATEST(DATEDIFF(v_end, v_start), 1);
    SET v_original = v_days * v_room_price;
    SET v_discount_amount = v_original * v_discount_rate;
    SET v_actual = v_discount_amount - v_prepay;

    INSERT INTO Checkout(
        CheckInId, CustomerId, RoomNo, OriginalAmount, DiscountRateSnapshot,
        DiscountAmount, PrepayAmount, ActualPayAmount, CheckoutTime, CashierId
    ) VALUES (
        p_checkin_id, v_customer_id, v_room_no, v_original, v_discount_rate,
        v_discount_amount, v_prepay, v_actual, p_checkout_time, p_cashier_id
    );

    SET p_checkout_id = LAST_INSERT_ID();

    CALL sp_add_operation_log(
        p_cashier_id,
        '办理结账',
        CONCAT('办理结账记录 ', p_checkout_id, '，入住订单ID ', p_checkin_id, '，结账时间 ', p_checkout_time)
    );

    COMMIT;
END$$

-- 5. 开始清扫
CREATE PROCEDURE sp_start_cleaning(
    IN p_task_id INT,
    IN p_cleaner_id INT
)
BEGIN
    DECLARE v_task_status VARCHAR(20);
    DECLARE v_cleaner_status VARCHAR(20);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT CleanStatus
    INTO v_task_status
    FROM CleaningTask
    WHERE CleaningTaskId = p_task_id
    FOR UPDATE;

    SELECT ApprovalStatus
    INTO v_cleaner_status
    FROM UserAccount
    WHERE AccountId = p_cleaner_id;

    IF v_cleaner_status <> '已启用' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '保洁员账号未启用';
    END IF;

    IF v_task_status <> '待清扫' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '只有待清扫任务可以开始处理';
    END IF;

    UPDATE CleaningTask
    SET CleanStatus = '清扫中',
        CleanerId = p_cleaner_id
    WHERE CleaningTaskId = p_task_id;

    CALL sp_add_operation_log(
        p_cleaner_id,
        '开始清扫',
        CONCAT('开始处理清扫任务 ', p_task_id)
    );

    COMMIT;
END$$

-- 6. 完成清扫
CREATE PROCEDURE sp_finish_cleaning(
    IN p_task_id INT,
    IN p_cleaner_id INT
)
BEGIN
    DECLARE v_task_status VARCHAR(20);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    SELECT CleanStatus
    INTO v_task_status
    FROM CleaningTask
    WHERE CleaningTaskId = p_task_id
    FOR UPDATE;

    IF v_task_status <> '清扫中' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '只有清扫中的任务可以完成';
    END IF;

    UPDATE CleaningTask
    SET CleanStatus = '已完成',
        CleanerId = p_cleaner_id,
        FinishTime = NOW()
    WHERE CleaningTaskId = p_task_id;

    CALL sp_add_operation_log(
        p_cleaner_id,
        '完成清扫',
        CONCAT('完成清扫任务 ', p_task_id)
    );

    COMMIT;
END$$

-- 7. 操作审计查询（只读，不需要事务）
CREATE PROCEDURE sp_operation_audit(
    IN p_operator_id INT,
    IN p_operation_type_name VARCHAR(50),
    IN p_start_time DATETIME,
    IN p_end_time DATETIME
)
BEGIN
    SELECT *
    FROM v_operation_audit
    WHERE (p_operator_id IS NULL OR AccountId = p_operator_id)
      AND (p_operation_type_name IS NULL OR OperationTypeName = p_operation_type_name)
      AND (p_start_time IS NULL OR OperationTime >= p_start_time)
      AND (p_end_time IS NULL OR OperationTime <= p_end_time)
    ORDER BY OperationTime DESC;
END$$
DELIMITER $$

CREATE PROCEDURE sp_change_room(
    IN p_checkin_id INT,
    IN p_new_room_id INT,
    IN p_operator_id INT
)
BEGIN
    DECLARE v_old_room_id INT;
    DECLARE v_old_room_no VARCHAR(30);
    DECLARE v_new_room_no VARCHAR(30);

    DECLARE v_operator_status VARCHAR(20);
    DECLARE v_new_room_status VARCHAR(20);
    DECLARE v_order_status VARCHAR(20);

    DECLARE v_not_found TINYINT DEFAULT 0;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_not_found = 1;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 1. 校验操作员
    SELECT ApprovalStatus
    INTO v_operator_status
    FROM UserAccount
    WHERE AccountId = p_operator_id
    FOR UPDATE;

    IF v_operator_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '操作员不存在';
    END IF;

    IF v_operator_status <> '已启用' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '操作员未启用';
    END IF;

    -- 2. 锁定入住订单
    SELECT ci.RoomId,
           r.RoomNo,
           ci.OrderStatus
    INTO v_old_room_id,
         v_old_room_no,
         v_order_status
    FROM CheckIn ci
    JOIN Room r ON ci.RoomId = r.RoomId
    WHERE ci.CheckInId = p_checkin_id
    FOR UPDATE;

    IF v_not_found = 1 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '入住订单不存在';
    END IF;

    IF v_order_status <> '进行中' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '只有进行中的入住订单允许换房';
    END IF;

    -- 3. 锁定新房间
    SELECT RoomStatus,
           RoomNo
    INTO v_new_room_status,
         v_new_room_no
    FROM Room
    WHERE RoomId = p_new_room_id
    FOR UPDATE;

    IF v_new_room_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '新房间不存在';
    END IF;

    IF v_new_room_status <> '空闲' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '新房间不是空闲状态';
    END IF;

    -- 防止换到同一个房间
    IF v_old_room_id = p_new_room_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '不能换到当前房间';
    END IF;

    -- 4. 更新入住订单房间
    UPDATE CheckIn
    SET RoomId = p_new_room_id
    WHERE CheckInId = p_checkin_id;

    -- 5. 更新房态
    UPDATE Room
    SET RoomStatus = '待清扫'
    WHERE RoomId = v_old_room_id;

    UPDATE Room
    SET RoomStatus = '已入住'
    WHERE RoomId = p_new_room_id;

    -- 6. 为旧房间生成清扫任务
    INSERT INTO CleaningTask(
        RoomId,
        RoomNo,
        TaskCreateTime,
        DeadlineTime,
        CleanStatus,
        CleanerId,
        FinishTime
    )
    VALUES(
        v_old_room_id,
        v_old_room_no,
        NOW(),
        DATE_ADD(NOW(), INTERVAL 2 HOUR),
        '待清扫',
        NULL,
        NULL
    )
    ON DUPLICATE KEY UPDATE
        RoomNo = VALUES(RoomNo),
        DeadlineTime = VALUES(DeadlineTime),
        CleanStatus = '待清扫';

    -- 7. 写操作日志
    CALL sp_add_operation_log(
        p_operator_id,
        '换房',
        CONCAT(
            '入住订单 ',
            p_checkin_id,
            ' 从房间 ',
            v_old_room_no,
            ' 换到房间 ',
            v_new_room_no
        )
    );

    COMMIT;

END$$

DELIMITER ;
