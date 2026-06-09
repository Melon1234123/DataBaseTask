DROP DATABASE IF EXISTS HotelSys;
CREATE DATABASE HotelSys
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_0900_ai_ci;
USE HotelSys;


CREATE TABLE Discount (
    DiscountId INT NOT NULL AUTO_INCREMENT COMMENT '折扣ID',
    DiscountGrade INT NOT NULL COMMENT '折扣等级',
    DiscountRate DECIMAL(5,4) NOT NULL DEFAULT 1.0000 COMMENT '折扣率',
    PRIMARY KEY (DiscountId),
    CONSTRAINT uk_discount_grade UNIQUE (DiscountGrade),
    CONSTRAINT ck_discount_rate CHECK (DiscountRate >= 0 AND DiscountRate <= 1)
) ENGINE=InnoDB COMMENT='折扣表';


CREATE TABLE AccountPermission (
    PermissionId INT NOT NULL AUTO_INCREMENT COMMENT '权限等级ID',
    PermissionName VARCHAR(50) NOT NULL COMMENT '权限名称',
    PermissionScope VARCHAR(1024) COMMENT '角色可访问功能范围',
    PRIMARY KEY (PermissionId),
    CONSTRAINT uk_permission_name UNIQUE (PermissionName)
) ENGINE=InnoDB COMMENT='账号权限表';
CREATE TABLE OperationType (
    OperationTypeId INT NOT NULL AUTO_INCREMENT COMMENT '操作类型ID',
    OperationTypeName VARCHAR(50) NOT NULL COMMENT '操作类型名称',
    PRIMARY KEY (OperationTypeId),
    CONSTRAINT uk_operation_type_name UNIQUE (OperationTypeName)
) ENGINE=InnoDB COMMENT='操作类型表';


CREATE TABLE RoomType (
    RoomTypeId INT NOT NULL AUTO_INCREMENT COMMENT '客房类型ID',
    RoomTypeName VARCHAR(50) NOT NULL COMMENT '客房类型名',
    RoomPrice DECIMAL(10,2) NOT NULL COMMENT '客房价格',
    PRIMARY KEY (RoomTypeId),
    CONSTRAINT uk_room_type_name UNIQUE (RoomTypeName),
    CONSTRAINT ck_room_type_price CHECK (RoomPrice >= 0)
) ENGINE=InnoDB COMMENT='客房类型表';


CREATE TABLE Customer (
    CustomerId INT NOT NULL AUTO_INCREMENT COMMENT '客户ID',
    CustomerName VARCHAR(50) NOT NULL COMMENT '客户姓名',
    CardId VARCHAR(30) NOT NULL COMMENT '身份证号',
    CustomerPhone VARCHAR(30) COMMENT '客户电话',
    Address VARCHAR(255) COMMENT '居住地址',
    DiscountId INT NOT NULL COMMENT '折扣ID',
    PRIMARY KEY (CustomerId),
    CONSTRAINT uk_customer_card UNIQUE (CardId),
    CONSTRAINT fk_customer_discount FOREIGN KEY (DiscountId)
        REFERENCES Discount(DiscountId)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='客户表';

CREATE TABLE UserAccount (
    AccountId INT NOT NULL AUTO_INCREMENT COMMENT '账号ID',
    AccountName VARCHAR(50) NOT NULL COMMENT '账号名',
    PasswordHash VARCHAR(255) NOT NULL COMMENT '账号密码哈希',
    Sex VARCHAR(10) COMMENT '性别',
    Birthday DATE COMMENT '生日',
    Phone VARCHAR(30) COMMENT '电话号码',
    PermissionId INT NOT NULL COMMENT '权限等级ID',
    SupervisorId INT NULL COMMENT '上级ID',
    ApprovalStatus VARCHAR(20) NOT NULL DEFAULT '待审核' COMMENT '账号审批状态',
    PRIMARY KEY (AccountId),
    CONSTRAINT uk_account_name UNIQUE (AccountName),
    CONSTRAINT ck_account_status CHECK (ApprovalStatus IN ('待审核', '已启用', '已驳回', '已停用')),
    CONSTRAINT fk_account_permission FOREIGN KEY (PermissionId)
        REFERENCES AccountPermission(PermissionId)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_account_supervisor FOREIGN KEY (SupervisorId)
        REFERENCES UserAccount(AccountId)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='用户账号表';

CREATE TABLE Room (
    RoomId INT NOT NULL AUTO_INCREMENT COMMENT '客房ID',
    RoomNo VARCHAR(30) NOT NULL COMMENT '房间号',
    FloorNo INT COMMENT '客房楼层',
    RoomPhone VARCHAR(30) COMMENT '客房电话',
    RoomTypeId INT NOT NULL COMMENT '客房类型ID',
    RoomStatus VARCHAR(20) NOT NULL DEFAULT '空闲' COMMENT '房间状态',
    PRIMARY KEY (RoomId),
    CONSTRAINT uk_room_no UNIQUE (RoomNo),
    CONSTRAINT ck_room_status CHECK (RoomStatus IN ('空闲', '已预定', '已入住', '待清扫', '停用')),
    CONSTRAINT fk_room_room_type FOREIGN KEY (RoomTypeId)
        REFERENCES RoomType(RoomTypeId)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='客房信息表';

CREATE TABLE Reservation (
    ReservationId INT NOT NULL AUTO_INCREMENT COMMENT '预定订单ID',
    ReserveTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '预定时间',
    ReserveStartTime DATETIME NOT NULL COMMENT '预定开始时间',
    ReserveEndTime DATETIME NOT NULL COMMENT '预定结束时间',
    PrepayAmount DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '预支付金额',
    GuestCount INT NOT NULL COMMENT '入住人数',
    RoomTypeId INT NOT NULL COMMENT '客房类型ID',
    CustomerId INT NOT NULL COMMENT '客户ID',
    OperatorId INT NOT NULL COMMENT '操作员ID',
    ReservationStatus VARCHAR(20) NOT NULL DEFAULT '未入住' COMMENT '预定状态',
    PRIMARY KEY (ReservationId),
    CONSTRAINT ck_reservation_status CHECK (ReservationStatus IN ('未入住', '已入住', '已取消')),
    CONSTRAINT ck_reservation_time CHECK (ReserveStartTime < ReserveEndTime AND ReserveTime <= ReserveStartTime),
    CONSTRAINT ck_reservation_guest CHECK (GuestCount > 0),
    CONSTRAINT ck_reservation_prepay CHECK (PrepayAmount >= 0),
    CONSTRAINT fk_reservation_room_type FOREIGN KEY (RoomTypeId)
        REFERENCES RoomType(RoomTypeId)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_reservation_customer FOREIGN KEY (CustomerId)
        REFERENCES Customer(CustomerId)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_reservation_operator FOREIGN KEY (OperatorId)
        REFERENCES UserAccount(AccountId)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='预定信息表';

CREATE TABLE CheckIn (
    CheckInId INT NOT NULL AUTO_INCREMENT COMMENT '入住订单ID',
    CheckInStartTime DATETIME NOT NULL COMMENT '入住开始时间',
    CheckInEndTime DATETIME NULL COMMENT '入住结束时间',
    GuestCount INT NOT NULL COMMENT '入住人数',
    PrepayAmount DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '预支付金额',
    OrderStatus VARCHAR(20) NOT NULL DEFAULT '进行中' COMMENT '订单状态',
    HandleTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '办理时间',
    CustomerId INT NOT NULL COMMENT '客户ID',
    RoomId INT NOT NULL COMMENT '客房ID',
    ReservationId INT NULL COMMENT '预定订单ID',
    OperatorId INT NOT NULL COMMENT '操作员ID',
    PRIMARY KEY (CheckInId),
    CONSTRAINT uk_checkin_reservation UNIQUE (ReservationId),
    CONSTRAINT ck_checkin_status CHECK (OrderStatus IN ('进行中', '已结束', '已取消')),
    CONSTRAINT ck_checkin_time CHECK (CheckInEndTime IS NULL OR CheckInEndTime > CheckInStartTime),
    CONSTRAINT ck_checkin_guest CHECK (GuestCount > 0),
    CONSTRAINT ck_checkin_prepay CHECK (PrepayAmount >= 0),
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
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='入住信息表';

CREATE TABLE Checkout (
    CheckoutId INT NOT NULL AUTO_INCREMENT COMMENT '结账ID',
    CheckInId INT NOT NULL COMMENT '入住订单ID',
    CustomerId INT NOT NULL COMMENT '客户ID',
    RoomNo VARCHAR(30) NOT NULL COMMENT '房间号快照',
    OriginalAmount DECIMAL(10,2) NOT NULL COMMENT '原支付金额',
    DiscountRateSnapshot DECIMAL(5,4) NOT NULL COMMENT '结账时折扣率',
    DiscountAmount DECIMAL(10,2) NOT NULL COMMENT '折后应支付金额',
    PrepayAmount DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '预支付金额',
    ActualPayAmount DECIMAL(10,2) NOT NULL COMMENT '实际应支付金额，负数表示退款',
    CheckoutTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '结账时间',
    CashierId INT NOT NULL COMMENT '收银员ID',
    PRIMARY KEY (CheckoutId),
    CONSTRAINT uk_checkout_checkin UNIQUE (CheckInId),
    CONSTRAINT ck_checkout_original CHECK (OriginalAmount >= 0),
    CONSTRAINT ck_checkout_rate CHECK (DiscountRateSnapshot >= 0 AND DiscountRateSnapshot <= 1),
    CONSTRAINT ck_checkout_discount CHECK (DiscountAmount >= 0),
    CONSTRAINT ck_checkout_prepay CHECK (PrepayAmount >= 0),
    CONSTRAINT fk_checkout_checkin FOREIGN KEY (CheckInId)
        REFERENCES CheckIn(CheckInId)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_checkout_customer FOREIGN KEY (CustomerId)
        REFERENCES Customer(CustomerId)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_checkout_cashier FOREIGN KEY (CashierId)
        REFERENCES UserAccount(AccountId)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='结账记录表';

CREATE TABLE OperationLog (
    OperationLogId INT NOT NULL AUTO_INCREMENT COMMENT '操作记录ID',
    OperatorId INT NOT NULL COMMENT '操作者ID',
    OperationTypeId INT NOT NULL COMMENT '操作类型ID',
    OperationInfo VARCHAR(1024) NOT NULL COMMENT '操作信息',
    OperationTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    PRIMARY KEY (OperationLogId),
    CONSTRAINT fk_operation_operator FOREIGN KEY (OperatorId)
        REFERENCES UserAccount(AccountId)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_operation_type FOREIGN KEY (OperationTypeId)
        REFERENCES OperationType(OperationTypeId)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='操作记录表';

CREATE TABLE CleaningTask (
    CleaningTaskId INT NOT NULL AUTO_INCREMENT COMMENT '清扫任务ID',
    RoomId INT NOT NULL COMMENT '客房ID',
    RoomNo VARCHAR(30) NOT NULL COMMENT '房间号快照',
    TaskCreateTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '任务发起时间',
    DeadlineTime DATETIME NULL COMMENT '任务截止时间',
    CleanStatus VARCHAR(20) NOT NULL DEFAULT '待清扫' COMMENT '清扫状态',
    CleanerId INT NULL COMMENT '保洁员ID',
    FinishTime DATETIME NULL COMMENT '完成时间',
    PRIMARY KEY (CleaningTaskId),
    CONSTRAINT uk_cleaning_one_unfinished_per_room UNIQUE (
        RoomId,
        (CASE WHEN CleanStatus <> '已完成' THEN 1 ELSE NULL END)
    ),
    CONSTRAINT ck_cleaning_status CHECK (CleanStatus IN ('待清扫', '清扫中', '已完成')),
    CONSTRAINT ck_cleaning_deadline CHECK (DeadlineTime IS NULL OR DeadlineTime > TaskCreateTime),
    CONSTRAINT fk_cleaning_room FOREIGN KEY (RoomId)
        REFERENCES Room(RoomId)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_cleaning_cleaner FOREIGN KEY (CleanerId)
        REFERENCES UserAccount(AccountId)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='清扫任务表';
