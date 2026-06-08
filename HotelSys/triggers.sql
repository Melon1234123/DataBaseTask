DELIMITER $$

CREATE TRIGGER trg_checkin_before_insert
BEFORE INSERT ON CheckIn
FOR EACH ROW
BEGIN
    DECLARE v_room_status VARCHAR(20);

    SELECT RoomStatus
    INTO v_room_status
    FROM Room
    WHERE RoomId = NEW.RoomId;

    IF v_room_status <> '空闲' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '客房不是空闲状态，不能新增入住订单';
    END IF;
END$$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER trg_checkin_after_insert
AFTER INSERT ON CheckIn
FOR EACH ROW
BEGIN
    IF NEW.OrderStatus = '进行中' THEN
        UPDATE Room
        SET RoomStatus = '已入住'
        WHERE RoomId = NEW.RoomId;

        IF NEW.ReservationId IS NOT NULL THEN
            UPDATE Reservation
            SET ReservationStatus = '已入住'
            WHERE ReservationId = NEW.ReservationId;
        END IF;
    END IF;
END$$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER trg_checkout_after_insert
AFTER INSERT ON Checkout
FOR EACH ROW
BEGIN
    DECLARE v_room_id INT;
    DECLARE v_room_no VARCHAR(30);

    SELECT ci.RoomId, r.RoomNo
    INTO v_room_id, v_room_no
    FROM CheckIn ci
    JOIN Room r ON ci.RoomId = r.RoomId
    WHERE ci.CheckInId = NEW.CheckInId;

    UPDATE CheckIn
    SET OrderStatus = '已结束',
        CheckInEndTime = NEW.CheckoutTime
    WHERE CheckInId = NEW.CheckInId;

    UPDATE Room
    SET RoomStatus = '待清扫'
    WHERE RoomId = v_room_id;

    INSERT INTO CleaningTask(RoomId, RoomNo, TaskCreateTime, DeadlineTime, CleanStatus, CleanerId, FinishTime)
    VALUES(v_room_id, v_room_no, NOW(), DATE_ADD(NOW(), INTERVAL 2 HOUR), '待清扫', NULL, NULL);
END$$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER trg_cleaning_after_update
AFTER UPDATE ON CleaningTask
FOR EACH ROW
BEGIN
    IF OLD.CleanStatus <> '已完成' AND NEW.CleanStatus = '已完成' THEN
        UPDATE Room
        SET RoomStatus = '空闲'
        WHERE RoomId = NEW.RoomId;
    END IF;
END$$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER trg_account_status_after_update
AFTER UPDATE ON UserAccount
FOR EACH ROW
BEGIN
    DECLARE v_operation_type_id INT;

    IF OLD.ApprovalStatus <> NEW.ApprovalStatus THEN
        SELECT OperationTypeId
        INTO v_operation_type_id
        FROM OperationType
        WHERE OperationTypeName = '账号审核';

        INSERT INTO OperationLog(OperatorId, OperationTypeId, OperationInfo, OperationTime)
        VALUES(
            NEW.AccountId,
            v_operation_type_id,
            CONCAT('账号状态由 ', OLD.ApprovalStatus, ' 变更为 ', NEW.ApprovalStatus),
            NOW()
        );
    END IF;
END$$

DELIMITER ;

