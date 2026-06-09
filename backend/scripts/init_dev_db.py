from pathlib import Path
import sys
from urllib.parse import parse_qs, unquote, urlparse

import pymysql
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402


def parse_mysql_url(url: str) -> dict:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or "root"),
        "password": unquote(parsed.password or ""),
        "database": (parsed.path or "/HotelSys").lstrip("/"),
        "charset": query.get("charset", ["utf8mb4"])[0],
    }


def execute_many(cursor, statements):
    for statement in statements:
        cursor.execute(statement)


def ensure_cleaning_unique_index(cursor):
    cursor.execute(
        """
        DELETE stale
        FROM CleaningTask stale
        JOIN (
            SELECT CleaningTaskId
            FROM (
                SELECT
                    CleaningTaskId,
                    ROW_NUMBER() OVER (
                        PARTITION BY RoomId
                        ORDER BY
                            CASE CleanStatus
                                WHEN '清扫中' THEN 0
                                WHEN '待清扫' THEN 1
                                ELSE 2
                            END,
                            CleaningTaskId DESC
                    ) AS row_num
                FROM CleaningTask
                WHERE CleanStatus <> '已完成'
            ) ranked
            WHERE ranked.row_num > 1
        ) duplicate_task
          ON duplicate_task.CleaningTaskId = stale.CleaningTaskId
        """
    )
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = 'CleaningTask'
          AND index_name = 'uk_cleaning_one_unfinished_per_room'
        """
    )
    if not cursor.fetchone()[0]:
        cursor.execute(
            """
            CREATE UNIQUE INDEX uk_cleaning_one_unfinished_per_room
            ON CleaningTask (
                RoomId,
                (CASE WHEN CleanStatus <> '已完成' THEN 1 ELSE NULL END)
            )
            """
        )


def reconcile_dev_data(cursor):
    cursor.execute(
        """
        UPDATE CheckIn ci
        JOIN Checkout co ON co.CheckInId = ci.CheckInId
        SET ci.OrderStatus = '已结束',
            ci.CheckInEndTime = COALESCE(ci.CheckInEndTime, co.CheckoutTime)
        WHERE ci.OrderStatus = '进行中'
        """
    )
    cursor.execute(
        """
        UPDATE Room r
        JOIN CheckIn ci ON ci.RoomId = r.RoomId
        JOIN Checkout co ON co.CheckInId = ci.CheckInId
        SET r.RoomStatus = '待清扫'
        WHERE ci.OrderStatus = '已结束'
          AND NOT EXISTS (
              SELECT 1
              FROM CleaningTask ct
              WHERE ct.RoomId = r.RoomId
                AND ct.CleanStatus = '已完成'
                AND ct.FinishTime >= co.CheckoutTime
          )
        """
    )


def create_schema(cursor):
    execute_many(
        cursor,
        [
            "DROP VIEW IF EXISTS v_operation_audit",
            "DROP VIEW IF EXISTS v_cleaning_task_queue",
            "DROP VIEW IF EXISTS v_checkout_bill",
            "DROP VIEW IF EXISTS v_checkin_detail",
            "DROP VIEW IF EXISTS v_reservation_detail",
            "DROP VIEW IF EXISTS v_room_status_overview",
            "DROP VIEW IF EXISTS v_available_room",
            "DROP PROCEDURE IF EXISTS sp_operation_audit",
            "DROP PROCEDURE IF EXISTS sp_finish_cleaning",
            "DROP PROCEDURE IF EXISTS sp_start_cleaning",
            "DROP PROCEDURE IF EXISTS sp_checkout",
            "DROP PROCEDURE IF EXISTS sp_check_in",
            "DROP PROCEDURE IF EXISTS sp_create_reservation",
            "DROP PROCEDURE IF EXISTS sp_add_operation_log",
            "DROP TRIGGER IF EXISTS trg_account_status_after_update",
            "DROP TRIGGER IF EXISTS trg_cleaning_after_update",
            "DROP TRIGGER IF EXISTS trg_checkout_after_insert",
            "DROP TRIGGER IF EXISTS trg_checkin_after_insert",
            "DROP TRIGGER IF EXISTS trg_checkin_before_insert",
            """
            CREATE TABLE IF NOT EXISTS Discount (
                DiscountId INT NOT NULL AUTO_INCREMENT,
                DiscountGrade INT NOT NULL,
                DiscountRate DECIMAL(5,4) NOT NULL DEFAULT 1.0000,
                PRIMARY KEY (DiscountId),
                UNIQUE KEY uk_discount_grade (DiscountGrade),
                CHECK (DiscountRate >= 0 AND DiscountRate <= 1)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS Customer (
                CustomerId INT NOT NULL AUTO_INCREMENT,
                CustomerName VARCHAR(50) NOT NULL,
                CardId VARCHAR(30) NOT NULL,
                CustomerPhone VARCHAR(30),
                Address VARCHAR(255),
                DiscountId INT NOT NULL,
                PRIMARY KEY (CustomerId),
                UNIQUE KEY uk_customer_card (CardId),
                KEY idx_customer_name_phone (CustomerName, CustomerPhone),
                KEY idx_customer_discount (DiscountId),
                CONSTRAINT fk_customer_discount FOREIGN KEY (DiscountId)
                    REFERENCES Discount(DiscountId)
                    ON DELETE RESTRICT ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS AccountPermission (
                PermissionId INT NOT NULL AUTO_INCREMENT,
                PermissionName VARCHAR(50) NOT NULL,
                PermissionScope VARCHAR(1024),
                PRIMARY KEY (PermissionId),
                UNIQUE KEY uk_permission_name (PermissionName)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS UserAccount (
                AccountId INT NOT NULL AUTO_INCREMENT,
                AccountName VARCHAR(50) NOT NULL,
                PasswordHash VARCHAR(255) NOT NULL,
                Sex VARCHAR(10),
                Birthday DATE,
                Phone VARCHAR(30),
                PermissionId INT NOT NULL,
                SupervisorId INT NULL,
                ApprovalStatus VARCHAR(20) NOT NULL DEFAULT '待审核',
                PRIMARY KEY (AccountId),
                UNIQUE KEY uk_account_name (AccountName),
                KEY idx_account_permission_status (PermissionId, ApprovalStatus),
                KEY idx_account_supervisor (SupervisorId),
                CONSTRAINT fk_account_permission FOREIGN KEY (PermissionId)
                    REFERENCES AccountPermission(PermissionId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CONSTRAINT fk_account_supervisor FOREIGN KEY (SupervisorId)
                    REFERENCES UserAccount(AccountId)
                    ON DELETE SET NULL ON UPDATE CASCADE,
                CHECK (ApprovalStatus IN ('待审核','已启用','已驳回','已停用'))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS RoomType (
                RoomTypeId INT NOT NULL AUTO_INCREMENT,
                RoomTypeName VARCHAR(50) NOT NULL,
                RoomPrice DECIMAL(10,2) NOT NULL,
                PRIMARY KEY (RoomTypeId),
                UNIQUE KEY uk_room_type_name (RoomTypeName),
                CHECK (RoomPrice >= 0)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS Room (
                RoomId INT NOT NULL AUTO_INCREMENT,
                RoomNo VARCHAR(30) NOT NULL,
                FloorNo INT,
                RoomPhone VARCHAR(30),
                RoomTypeId INT NOT NULL,
                RoomStatus VARCHAR(20) NOT NULL DEFAULT '空闲',
                PRIMARY KEY (RoomId),
                UNIQUE KEY uk_room_no (RoomNo),
                KEY idx_room_type_status (RoomTypeId, RoomStatus),
                CONSTRAINT fk_room_type FOREIGN KEY (RoomTypeId)
                    REFERENCES RoomType(RoomTypeId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CHECK (RoomStatus IN ('空闲','已预定','已入住','待清扫','停用'))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS Reservation (
                ReservationId INT NOT NULL AUTO_INCREMENT,
                ReserveTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ReserveStartTime DATETIME NOT NULL,
                ReserveEndTime DATETIME NOT NULL,
                PrepayAmount DECIMAL(10,2) NOT NULL DEFAULT 0,
                GuestCount INT NOT NULL,
                RoomTypeId INT NOT NULL,
                CustomerId INT NOT NULL,
                OperatorId INT NOT NULL,
                ReservationStatus VARCHAR(20) NOT NULL DEFAULT '未入住',
                PRIMARY KEY (ReservationId),
                KEY idx_reservation_customer_status_time (CustomerId, ReservationStatus, ReserveStartTime),
                KEY idx_reservation_room_type (RoomTypeId),
                CONSTRAINT fk_reservation_room_type FOREIGN KEY (RoomTypeId)
                    REFERENCES RoomType(RoomTypeId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CONSTRAINT fk_reservation_customer FOREIGN KEY (CustomerId)
                    REFERENCES Customer(CustomerId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CONSTRAINT fk_reservation_operator FOREIGN KEY (OperatorId)
                    REFERENCES UserAccount(AccountId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CHECK (ReserveStartTime < ReserveEndTime),
                CHECK (GuestCount > 0),
                CHECK (PrepayAmount >= 0),
                CHECK (ReservationStatus IN ('未入住','已入住','已取消'))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS CheckIn (
                CheckInId INT NOT NULL AUTO_INCREMENT,
                CheckInStartTime DATETIME NOT NULL,
                CheckInEndTime DATETIME NULL,
                GuestCount INT NOT NULL,
                PrepayAmount DECIMAL(10,2) NOT NULL DEFAULT 0,
                OrderStatus VARCHAR(20) NOT NULL DEFAULT '进行中',
                HandleTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CustomerId INT NOT NULL,
                RoomId INT NOT NULL,
                ReservationId INT NULL,
                OperatorId INT NOT NULL,
                PRIMARY KEY (CheckInId),
                UNIQUE KEY uk_checkin_reservation (ReservationId),
                KEY idx_checkin_customer_status_time (CustomerId, OrderStatus, CheckInStartTime),
                KEY idx_checkin_room (RoomId),
                CONSTRAINT fk_checkin_customer FOREIGN KEY (CustomerId)
                    REFERENCES Customer(CustomerId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CONSTRAINT fk_checkin_room FOREIGN KEY (RoomId)
                    REFERENCES Room(RoomId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CONSTRAINT fk_checkin_reservation FOREIGN KEY (ReservationId)
                    REFERENCES Reservation(ReservationId)
                    ON DELETE SET NULL ON UPDATE CASCADE,
                CONSTRAINT fk_checkin_operator FOREIGN KEY (OperatorId)
                    REFERENCES UserAccount(AccountId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CHECK (CheckInEndTime IS NULL OR CheckInEndTime > CheckInStartTime),
                CHECK (GuestCount > 0),
                CHECK (PrepayAmount >= 0),
                CHECK (OrderStatus IN ('进行中','已结束','已取消'))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS Checkout (
                CheckoutId INT NOT NULL AUTO_INCREMENT,
                CheckInId INT NOT NULL,
                CustomerId INT NOT NULL,
                RoomNo VARCHAR(30) NOT NULL,
                OriginalAmount DECIMAL(10,2) NOT NULL,
                DiscountRateSnapshot DECIMAL(5,4) NOT NULL,
                DiscountAmount DECIMAL(10,2) NOT NULL,
                PrepayAmount DECIMAL(10,2) NOT NULL DEFAULT 0,
                ActualPayAmount DECIMAL(10,2) NOT NULL,
                CheckoutTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CashierId INT NOT NULL,
                PRIMARY KEY (CheckoutId),
                UNIQUE KEY uk_checkout_checkin (CheckInId),
                KEY idx_checkout_customer_time (CustomerId, CheckoutTime),
                KEY idx_checkout_cashier_time (CashierId, CheckoutTime),
                CONSTRAINT fk_checkout_checkin FOREIGN KEY (CheckInId)
                    REFERENCES CheckIn(CheckInId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CONSTRAINT fk_checkout_customer FOREIGN KEY (CustomerId)
                    REFERENCES Customer(CustomerId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CONSTRAINT fk_checkout_cashier FOREIGN KEY (CashierId)
                    REFERENCES UserAccount(AccountId)
                    ON DELETE RESTRICT ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS OperationType (
                OperationTypeId INT NOT NULL AUTO_INCREMENT,
                OperationTypeName VARCHAR(50) NOT NULL,
                PRIMARY KEY (OperationTypeId),
                UNIQUE KEY uk_operation_type_name (OperationTypeName)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS OperationLog (
                OperationLogId INT NOT NULL AUTO_INCREMENT,
                OperatorId INT NOT NULL,
                OperationTypeId INT NOT NULL,
                OperationInfo VARCHAR(1024) NOT NULL,
                OperationTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (OperationLogId),
                KEY idx_operation_operator_time (OperatorId, OperationTime),
                KEY idx_operation_type_time (OperationTypeId, OperationTime),
                CONSTRAINT fk_log_operator FOREIGN KEY (OperatorId)
                    REFERENCES UserAccount(AccountId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CONSTRAINT fk_log_type FOREIGN KEY (OperationTypeId)
                    REFERENCES OperationType(OperationTypeId)
                    ON DELETE RESTRICT ON UPDATE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS CleaningTask (
                CleaningTaskId INT NOT NULL AUTO_INCREMENT,
                RoomId INT NOT NULL,
                RoomNo VARCHAR(30) NOT NULL,
                TaskCreateTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                DeadlineTime DATETIME NULL,
                CleanStatus VARCHAR(20) NOT NULL DEFAULT '待清扫',
                CleanerId INT NULL,
                FinishTime DATETIME NULL,
                PRIMARY KEY (CleaningTaskId),
                UNIQUE KEY uk_cleaning_one_unfinished_per_room (
                    RoomId,
                    (CASE WHEN CleanStatus <> '已完成' THEN 1 ELSE NULL END)
                ),
                KEY idx_cleaning_status_deadline (CleanStatus, DeadlineTime),
                KEY idx_cleaning_cleaner_status (CleanerId, CleanStatus),
                CONSTRAINT fk_cleaning_room FOREIGN KEY (RoomId)
                    REFERENCES Room(RoomId)
                    ON DELETE RESTRICT ON UPDATE CASCADE,
                CONSTRAINT fk_cleaning_cleaner FOREIGN KEY (CleanerId)
                    REFERENCES UserAccount(AccountId)
                    ON DELETE SET NULL ON UPDATE CASCADE,
                CHECK (CleanStatus IN ('待清扫','清扫中','已完成'))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
        ],
    )


def seed_data(cursor):
    password_hash = hash_password("123456")
    seed_passwords = {
        "admin_hash": password_hash,
        "front_hash": password_hash,
        "cleaner_hash": password_hash,
        "auditor_hash": password_hash,
    }

    execute_many(
        cursor,
        [
            """
            INSERT INTO Discount(DiscountId, DiscountGrade, DiscountRate) VALUES
            (1, 0, 1.0000), (2, 1, 0.9500), (3, 2, 0.9000), (4, 3, 0.8500)
            ON DUPLICATE KEY UPDATE
                DiscountGrade = VALUES(DiscountGrade),
                DiscountRate = VALUES(DiscountRate)
            """,
            """
            INSERT INTO AccountPermission(PermissionId, PermissionName, PermissionScope) VALUES
            (1, '管理员', '账号审核、客房管理、客户管理、预定管理、入住管理、结账管理、操作审计、清扫任务管理'),
            (2, '前台工作人员', '客户管理、预定管理、入住管理、结账管理、清扫任务查询'),
            (3, '保洁员', '清扫任务查询、清扫开始、清扫完成'),
            (4, '审计员', '操作记录查询、账单查询')
            ON DUPLICATE KEY UPDATE
                PermissionName = VALUES(PermissionName),
                PermissionScope = VALUES(PermissionScope)
            """,
            """
            INSERT INTO OperationType(OperationTypeId, OperationTypeName) VALUES
            (1, '创建预定'),
            (2, '办理入住'),
            (3, '办理结账'),
            (4, '开始清扫'),
            (5, '完成清扫'),
            (6, '账号审核'),
            (7, '客房维护'),
            (8, '客户维护'),
            (9, '换房'),
            (10, '系统初始化')
            ON DUPLICATE KEY UPDATE OperationTypeName = VALUES(OperationTypeName)
            """,
        ],
    )

    cursor.execute(
        """
        INSERT INTO UserAccount(
            AccountId, AccountName, PasswordHash, Sex, Birthday, Phone,
            PermissionId, SupervisorId, ApprovalStatus
        ) VALUES
        (1, 'admin01', %(admin_hash)s, '男', '2000-01-01', '13800000001', 1, NULL, '已启用'),
        (2, 'front01', %(front_hash)s, '女', '2001-02-02', '13800000002', 2, 1, '已启用'),
        (3, 'cleaner01', %(cleaner_hash)s, '女', '2002-03-03', '13800000003', 3, 1, '待审核'),
        (4, 'auditor01', %(auditor_hash)s, '男', '2003-04-04', '13800000004', 4, 1, '已启用')
        ON DUPLICATE KEY UPDATE
            PasswordHash = VALUES(PasswordHash),
            Sex = VALUES(Sex),
            Birthday = VALUES(Birthday),
            Phone = VALUES(Phone),
            PermissionId = VALUES(PermissionId),
            SupervisorId = VALUES(SupervisorId),
            ApprovalStatus = VALUES(ApprovalStatus)
        """,
        seed_passwords,
    )

    execute_many(
        cursor,
        [
            """
            INSERT INTO Customer(CustomerId, CustomerName, CardId, CustomerPhone, Address, DiscountId) VALUES
            (1001, '张三', '110101199001011234', '13800010001', '北京市朝阳区', 1),
            (1002, '李秋', '330102200202020022', '13800010002', '杭州市西湖区', 2),
            (1003, '王晨', '330102200303030033', '13800010003', '宁波市鄞州区', 3)
            ON DUPLICATE KEY UPDATE
                CustomerName = VALUES(CustomerName),
                CustomerPhone = VALUES(CustomerPhone),
                Address = VALUES(Address),
                DiscountId = VALUES(DiscountId)
            """,
            """
            INSERT INTO RoomType(RoomTypeId, RoomTypeName, RoomPrice) VALUES
            (1, '标准间', 220.00),
            (2, '大床房', 280.00),
            (3, '家庭套房', 480.00)
            ON DUPLICATE KEY UPDATE
                RoomTypeName = VALUES(RoomTypeName),
                RoomPrice = VALUES(RoomPrice)
            """,
            """
            INSERT INTO Room(RoomId, RoomNo, FloorNo, RoomPhone, RoomTypeId, RoomStatus) VALUES
            (2001, '101', 1, '8101', 1, '空闲'),
            (2002, '102', 1, '8102', 1, '已入住'),
            (2003, '201', 2, '8201', 2, '空闲'),
            (2004, '202', 2, '8202', 2, '待清扫'),
            (2005, '301', 3, '8301', 3, '空闲'),
            (2006, '302', 3, '8302', 3, '停用')
            ON DUPLICATE KEY UPDATE
                RoomNo = VALUES(RoomNo),
                FloorNo = VALUES(FloorNo),
                RoomPhone = VALUES(RoomPhone),
                RoomTypeId = VALUES(RoomTypeId),
                RoomStatus = VALUES(RoomStatus)
            """,
            """
            INSERT INTO Reservation(
                ReservationId, CustomerId, RoomTypeId, ReserveTime,
                ReserveStartTime, ReserveEndTime, GuestCount, PrepayAmount,
                OperatorId, ReservationStatus
            ) VALUES (
                3001, 1001, 1, '2026-06-08 10:30:00',
                '2026-06-09 14:00:00', '2026-06-11 12:00:00',
                2, 200.00, 2, '未入住'
            )
            ON DUPLICATE KEY UPDATE
                CustomerId = VALUES(CustomerId),
                RoomTypeId = VALUES(RoomTypeId),
                ReserveStartTime = VALUES(ReserveStartTime),
                ReserveEndTime = VALUES(ReserveEndTime),
                GuestCount = VALUES(GuestCount),
                PrepayAmount = VALUES(PrepayAmount),
                OperatorId = VALUES(OperatorId),
                ReservationStatus = VALUES(ReservationStatus)
            """,
            """
            INSERT INTO CheckIn(
                CheckInId, CustomerId, RoomId, ReservationId,
                CheckInStartTime, CheckInEndTime, GuestCount,
                PrepayAmount, OrderStatus, OperatorId
            ) VALUES (
                4001, 1003, 2002, NULL,
                '2026-06-08 14:00:00', NULL, 2,
                300.00, '进行中', 2
            )
            ON DUPLICATE KEY UPDATE
                CustomerId = VALUES(CustomerId),
                RoomId = VALUES(RoomId),
                CheckInStartTime = VALUES(CheckInStartTime),
                CheckInEndTime = IF(
                    EXISTS(SELECT 1 FROM Checkout WHERE Checkout.CheckInId = CheckIn.CheckInId),
                    CheckIn.CheckInEndTime,
                    VALUES(CheckInEndTime)
                ),
                GuestCount = VALUES(GuestCount),
                PrepayAmount = VALUES(PrepayAmount),
                OrderStatus = IF(
                    EXISTS(SELECT 1 FROM Checkout WHERE Checkout.CheckInId = CheckIn.CheckInId),
                    CheckIn.OrderStatus,
                    VALUES(OrderStatus)
                ),
                OperatorId = VALUES(OperatorId)
            """,
            """
            INSERT INTO CleaningTask(
                CleaningTaskId, RoomId, RoomNo, DeadlineTime,
                CleanStatus, CleanerId, FinishTime
            ) VALUES (
                6001, 2004, '202', DATE_ADD(NOW(), INTERVAL 4 HOUR),
                '待清扫', 3, NULL
            )
            ON DUPLICATE KEY UPDATE
                RoomId = VALUES(RoomId),
                RoomNo = VALUES(RoomNo),
                DeadlineTime = VALUES(DeadlineTime),
                CleanStatus = VALUES(CleanStatus),
                CleanerId = VALUES(CleanerId),
                FinishTime = VALUES(FinishTime)
            """,
            """
            INSERT INTO OperationLog(OperationLogId, OperatorId, OperationTypeId, OperationInfo, OperationTime)
            VALUES (1, 1, 10, '加载真实接口前端对应的开发数据库种子数据', NOW())
            ON DUPLICATE KEY UPDATE
                OperatorId = VALUES(OperatorId),
                OperationTypeId = VALUES(OperationTypeId),
                OperationInfo = VALUES(OperationInfo),
                OperationTime = VALUES(OperationTime)
            """,
        ],
    )


def create_views_and_routines(cursor):
    execute_many(
        cursor,
        [
            """
            CREATE OR REPLACE VIEW v_available_room AS
            SELECT
                r.RoomId, r.RoomNo, r.FloorNo, r.RoomPhone,
                rt.RoomTypeId, rt.RoomTypeName, rt.RoomPrice, r.RoomStatus
            FROM Room r
            JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
            WHERE r.RoomStatus = '空闲'
            """,
            """
            CREATE OR REPLACE VIEW v_room_status_overview AS
            SELECT rt.RoomTypeName, r.RoomStatus, COUNT(*) AS RoomCount
            FROM Room r
            JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
            GROUP BY rt.RoomTypeName, r.RoomStatus
            """,
            """
            CREATE OR REPLACE VIEW v_reservation_detail AS
            SELECT
                rv.ReservationId, c.CustomerId, c.CustomerName, c.CardId,
                c.CustomerPhone, rt.RoomTypeId, rt.RoomTypeName,
                rv.ReserveTime, rv.ReserveStartTime, rv.ReserveEndTime,
                rv.PrepayAmount, rv.GuestCount, rv.ReservationStatus,
                ua.AccountName AS OperatorName
            FROM Reservation rv
            JOIN Customer c ON rv.CustomerId = c.CustomerId
            JOIN RoomType rt ON rv.RoomTypeId = rt.RoomTypeId
            JOIN UserAccount ua ON rv.OperatorId = ua.AccountId
            """,
            """
            CREATE OR REPLACE VIEW v_checkin_detail AS
            SELECT
                ci.CheckInId, ci.CustomerId, c.CustomerName, c.CardId,
                ci.RoomId, r.RoomNo, rt.RoomTypeName, ci.CheckInStartTime,
                ci.CheckInEndTime, ci.GuestCount, ci.PrepayAmount,
                ci.OrderStatus, ci.HandleTime, ci.ReservationId,
                ua.AccountName AS OperatorName
            FROM CheckIn ci
            JOIN Customer c ON ci.CustomerId = c.CustomerId
            JOIN Room r ON ci.RoomId = r.RoomId
            JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
            LEFT JOIN UserAccount ua ON ci.OperatorId = ua.AccountId
            """,
            """
            CREATE OR REPLACE VIEW v_checkout_bill AS
            SELECT
                co.CheckoutId, co.CheckInId, co.CustomerId, c.CustomerName,
                c.CardId, co.RoomNo, co.OriginalAmount,
                co.DiscountRateSnapshot, co.DiscountAmount, co.PrepayAmount,
                co.ActualPayAmount, co.CheckoutTime, co.CashierId,
                ua.AccountName AS CashierName
            FROM Checkout co
            JOIN Customer c ON co.CustomerId = c.CustomerId
            JOIN UserAccount ua ON co.CashierId = ua.AccountId
            """,
            """
            CREATE OR REPLACE VIEW v_cleaning_task_queue AS
            SELECT
                ct.CleaningTaskId, ct.RoomId, ct.RoomNo, rt.RoomTypeName,
                ct.TaskCreateTime, ct.DeadlineTime, ct.CleanStatus,
                ct.CleanerId, ua.AccountName AS CleanerName, ct.FinishTime
            FROM CleaningTask ct
            JOIN Room r ON ct.RoomId = r.RoomId
            JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
            LEFT JOIN UserAccount ua ON ct.CleanerId = ua.AccountId
            """,
            """
            CREATE OR REPLACE VIEW v_operation_audit AS
            SELECT
                ol.OperationLogId, ua.AccountId, ua.AccountName,
                ap.PermissionName, ot.OperationTypeName,
                ol.OperationInfo, ol.OperationTime
            FROM OperationLog ol
            JOIN UserAccount ua ON ol.OperatorId = ua.AccountId
            JOIN AccountPermission ap ON ua.PermissionId = ap.PermissionId
            JOIN OperationType ot ON ol.OperationTypeId = ot.OperationTypeId
            """,
            """
            CREATE PROCEDURE sp_add_operation_log(
                IN p_operator_id INT,
                IN p_operation_type_name VARCHAR(50),
                IN p_operation_info VARCHAR(1024)
            )
            BEGIN
                DECLARE v_operation_type_id INT DEFAULT NULL;
                SELECT OperationTypeId INTO v_operation_type_id
                FROM OperationType
                WHERE OperationTypeName = p_operation_type_name;
                IF v_operation_type_id IS NULL THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '操作类型不存在，不能写入操作日志';
                END IF;
                INSERT INTO OperationLog(OperatorId, OperationTypeId, OperationInfo, OperationTime)
                VALUES(p_operator_id, v_operation_type_id, p_operation_info, NOW());
            END
            """,
            """
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
                SELECT ApprovalStatus INTO v_operator_status
                FROM UserAccount WHERE AccountId = p_operator_id;
                IF COALESCE(v_operator_status, '') <> '已启用' THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '操作员账号未启用，不能创建预定';
                END IF;
                IF p_start_time >= p_end_time THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '预定开始时间必须早于结束时间';
                END IF;
                IF p_guest_count <= 0 OR p_prepay < 0 THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '入住人数或预支付金额非法';
                END IF;
                INSERT INTO Reservation(
                    CustomerId, RoomTypeId, OperatorId, ReserveStartTime,
                    ReserveEndTime, GuestCount, PrepayAmount, ReservationStatus
                )
                VALUES(
                    p_customer_id, p_room_type_id, p_operator_id,
                    p_start_time, p_end_time, p_guest_count, p_prepay, '未入住'
                );
                SET p_reservation_id = LAST_INSERT_ID();
                CALL sp_add_operation_log(
                    p_operator_id,
                    '创建预定',
                    CONCAT('创建预定 ', p_reservation_id, '，客户ID ', p_customer_id)
                );
            END
            """,
            """
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
                DECLARE v_reservation_status VARCHAR(20);
                SELECT RoomStatus INTO v_room_status
                FROM Room WHERE RoomId = p_room_id FOR UPDATE;
                IF COALESCE(v_room_status, '') <> '空闲' THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '客房当前不是空闲状态，不能办理入住';
                END IF;
                SELECT ApprovalStatus INTO v_operator_status
                FROM UserAccount WHERE AccountId = p_operator_id;
                IF COALESCE(v_operator_status, '') <> '已启用' THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '操作员账号未启用，不能办理入住';
                END IF;
                IF p_reservation_id IS NOT NULL THEN
                    SELECT ReservationStatus INTO v_reservation_status
                    FROM Reservation WHERE ReservationId = p_reservation_id FOR UPDATE;
                    IF COALESCE(v_reservation_status, '') <> '未入住' THEN
                        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '预定状态不是未入住，不能转入住';
                    END IF;
                END IF;
                IF p_guest_count <= 0 OR p_prepay < 0 THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '入住人数或预支付金额非法';
                END IF;
                INSERT INTO CheckIn(
                    CheckInStartTime, CheckInEndTime, GuestCount,
                    PrepayAmount, OrderStatus, CustomerId, RoomId,
                    ReservationId, OperatorId
                )
                VALUES(
                    p_start_time, p_end_time, p_guest_count,
                    p_prepay, '进行中', p_customer_id, p_room_id,
                    p_reservation_id, p_operator_id
                );
                SET p_checkin_id = LAST_INSERT_ID();
                CALL sp_add_operation_log(
                    p_operator_id,
                    '办理入住',
                    CONCAT('办理入住订单 ', p_checkin_id, '，房间ID ', p_room_id)
                );
            END
            """,
            """
            CREATE PROCEDURE sp_checkout(
                IN p_checkin_id INT,
                IN p_cashier_id INT,
                IN p_checkout_time DATETIME,
                OUT p_checkout_id INT
            )
            BEGIN
                DECLARE v_customer_id INT;
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
                DECLARE v_status VARCHAR(20);

                SELECT
                    ci.CustomerId, ci.RoomId, r.RoomNo, rt.RoomPrice,
                    d.DiscountRate, ci.PrepayAmount, ci.CheckInStartTime,
                    COALESCE(ci.CheckInEndTime, p_checkout_time), ci.OrderStatus
                INTO
                    v_customer_id, v_room_id, v_room_no, v_room_price,
                    v_discount_rate, v_prepay, v_start, v_end, v_status
                FROM CheckIn ci
                JOIN Room r ON ci.RoomId = r.RoomId
                JOIN RoomType rt ON r.RoomTypeId = rt.RoomTypeId
                JOIN Customer c ON ci.CustomerId = c.CustomerId
                JOIN Discount d ON c.DiscountId = d.DiscountId
                WHERE ci.CheckInId = p_checkin_id
                FOR UPDATE;

                IF COALESCE(v_status, '') <> '进行中' THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '只有进行中的入住订单可以结账';
                END IF;
                IF v_start > p_checkout_time THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '结账时间不能早于入住开始时间';
                END IF;
                IF v_start = p_checkout_time THEN
                    SET p_checkout_time = DATE_ADD(v_start, INTERVAL 1 SECOND);
                END IF;

                SET v_days = GREATEST(1, CEIL(TIMESTAMPDIFF(SECOND, v_start, v_end) / 86400));
                SET v_original = ROUND(v_room_price * v_days, 2);
                SET v_discount_amount = ROUND(v_original * v_discount_rate, 2);
                SET v_actual = ROUND(v_discount_amount - v_prepay, 2);

                INSERT INTO Checkout(
                    CheckInId, CustomerId, RoomNo, OriginalAmount,
                    DiscountRateSnapshot, DiscountAmount, PrepayAmount,
                    ActualPayAmount, CheckoutTime, CashierId
                )
                VALUES(
                    p_checkin_id, v_customer_id, v_room_no, v_original,
                    v_discount_rate, v_discount_amount, v_prepay,
                    v_actual, p_checkout_time, p_cashier_id
                );
                SET p_checkout_id = LAST_INSERT_ID();
                CALL sp_add_operation_log(
                    p_cashier_id,
                    '办理结账',
                    CONCAT('办理结账记录 ', p_checkout_id, '，入住订单ID ', p_checkin_id)
                );
            END
            """,
            """
            CREATE PROCEDURE sp_start_cleaning(
                IN p_task_id INT,
                IN p_cleaner_id INT
            )
            BEGIN
                DECLARE v_task_status VARCHAR(20);
                DECLARE v_cleaner_status VARCHAR(20);
                SELECT CleanStatus INTO v_task_status
                FROM CleaningTask WHERE CleaningTaskId = p_task_id FOR UPDATE;
                SELECT ApprovalStatus INTO v_cleaner_status
                FROM UserAccount WHERE AccountId = p_cleaner_id;
                IF COALESCE(v_cleaner_status, '') <> '已启用' THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '保洁员账号未启用';
                END IF;
                IF COALESCE(v_task_status, '') <> '待清扫' THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '只有待清扫任务可以开始';
                END IF;
                UPDATE CleaningTask
                SET CleanStatus = '清扫中', CleanerId = p_cleaner_id
                WHERE CleaningTaskId = p_task_id;
                CALL sp_add_operation_log(p_cleaner_id, '开始清扫', CONCAT('开始清扫任务 ', p_task_id));
            END
            """,
            """
            CREATE PROCEDURE sp_finish_cleaning(
                IN p_task_id INT,
                IN p_cleaner_id INT
            )
            BEGIN
                DECLARE v_task_status VARCHAR(20);
                SELECT CleanStatus INTO v_task_status
                FROM CleaningTask WHERE CleaningTaskId = p_task_id FOR UPDATE;
                IF COALESCE(v_task_status, '') <> '清扫中' THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '只有清扫中的任务可以完成';
                END IF;
                UPDATE CleaningTask
                SET CleanStatus = '已完成', CleanerId = p_cleaner_id, FinishTime = NOW()
                WHERE CleaningTaskId = p_task_id;
                CALL sp_add_operation_log(p_cleaner_id, '完成清扫', CONCAT('完成清扫任务 ', p_task_id));
            END
            """,
            """
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
            END
            """,
            """
            CREATE TRIGGER trg_checkin_before_insert
            BEFORE INSERT ON CheckIn
            FOR EACH ROW
            BEGIN
                DECLARE v_room_status VARCHAR(20);
                SELECT RoomStatus INTO v_room_status
                FROM Room WHERE RoomId = NEW.RoomId;
                IF v_room_status <> '空闲' THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '客房不是空闲状态，不能新增入住订单';
                END IF;
            END
            """,
            """
            CREATE TRIGGER trg_checkin_after_insert
            AFTER INSERT ON CheckIn
            FOR EACH ROW
            BEGIN
                IF NEW.OrderStatus = '进行中' THEN
                    UPDATE Room SET RoomStatus = '已入住'
                    WHERE RoomId = NEW.RoomId;
                    IF NEW.ReservationId IS NOT NULL THEN
                        UPDATE Reservation SET ReservationStatus = '已入住'
                        WHERE ReservationId = NEW.ReservationId;
                    END IF;
                END IF;
            END
            """,
            """
            CREATE TRIGGER trg_checkout_after_insert
            AFTER INSERT ON Checkout
            FOR EACH ROW
            BEGIN
                DECLARE v_room_id INT;
                DECLARE v_room_no VARCHAR(30);
                SELECT ci.RoomId, r.RoomNo INTO v_room_id, v_room_no
                FROM CheckIn ci
                JOIN Room r ON ci.RoomId = r.RoomId
                WHERE ci.CheckInId = NEW.CheckInId;
                UPDATE CheckIn
                SET OrderStatus = '已结束', CheckInEndTime = NEW.CheckoutTime
                WHERE CheckInId = NEW.CheckInId;
                UPDATE Room SET RoomStatus = '待清扫'
                WHERE RoomId = v_room_id;
                INSERT INTO CleaningTask(RoomId, RoomNo, TaskCreateTime, DeadlineTime, CleanStatus)
                VALUES(v_room_id, v_room_no, NEW.CheckoutTime, DATE_ADD(NEW.CheckoutTime, INTERVAL 4 HOUR), '待清扫')
                ON DUPLICATE KEY UPDATE
                    RoomNo = VALUES(RoomNo),
                    DeadlineTime = VALUES(DeadlineTime),
                    CleanStatus = '待清扫';
            END
            """,
            """
            CREATE TRIGGER trg_cleaning_after_update
            AFTER UPDATE ON CleaningTask
            FOR EACH ROW
            BEGIN
                IF OLD.CleanStatus <> '已完成' AND NEW.CleanStatus = '已完成' THEN
                    UPDATE Room SET RoomStatus = '空闲'
                    WHERE RoomId = NEW.RoomId;
                END IF;
            END
            """,
            """
            CREATE TRIGGER trg_account_status_after_update
            AFTER UPDATE ON UserAccount
            FOR EACH ROW
            BEGIN
                DECLARE v_operation_type_id INT;
                IF OLD.ApprovalStatus <> NEW.ApprovalStatus THEN
                    SELECT OperationTypeId INTO v_operation_type_id
                    FROM OperationType WHERE OperationTypeName = '账号审核';
                    INSERT INTO OperationLog(OperatorId, OperationTypeId, OperationInfo, OperationTime)
                    VALUES(
                        NEW.AccountId,
                        v_operation_type_id,
                        CONCAT('账号状态由 ', OLD.ApprovalStatus, ' 变更为 ', NEW.ApprovalStatus),
                        NOW()
                    );
                END IF;
            END
            """,
        ],
    )


def main():
    load_dotenv(ROOT_DIR / ".env")
    settings = get_settings()
    config = parse_mysql_url(settings.database_url)
    db_name = config.pop("database")

    server_conn = pymysql.connect(**config, autocommit=True)
    try:
        with server_conn.cursor() as cursor:
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS `%s` DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_0900_ai_ci"
                % db_name
            )
    finally:
        server_conn.close()

    db_conn = pymysql.connect(**config, database=db_name, autocommit=True)
    try:
        with db_conn.cursor() as cursor:
            create_schema(cursor)
            seed_data(cursor)
            reconcile_dev_data(cursor)
            ensure_cleaning_unique_index(cursor)
            create_views_and_routines(cursor)
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            print("Initialized %s with %s tables." % (db_name, len(tables)))
    finally:
        db_conn.close()


if __name__ == "__main__":
    main()
