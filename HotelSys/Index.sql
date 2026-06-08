-- Customer 表
CREATE INDEX idx_customer_name_phone ON Customer(CustomerName, CustomerPhone);
CREATE INDEX idx_customer_discount ON Customer(DiscountId);

-- UserAccount 表
CREATE INDEX idx_account_permission_status ON UserAccount(PermissionId, ApprovalStatus);
CREATE INDEX idx_account_supervisor ON UserAccount(SupervisorId);

-- Room 表
CREATE INDEX idx_room_type_status ON Room(RoomTypeId, RoomStatus);
CREATE INDEX idx_room_status ON Room(RoomStatus);

-- Reservation 表
CREATE INDEX idx_reservation_customer_status_time ON Reservation(CustomerId, ReservationStatus, ReserveStartTime);
CREATE INDEX idx_reservation_roomtype_status_time ON Reservation(RoomTypeId, ReservationStatus, ReserveStartTime);
CREATE INDEX idx_reservation_operator ON Reservation(OperatorId);

-- CheckIn 表
CREATE INDEX idx_checkin_customer ON CheckIn(CustomerId);
CREATE INDEX idx_checkin_room_status ON CheckIn(RoomId, OrderStatus);
CREATE INDEX idx_checkin_operator_time ON CheckIn(OperatorId, HandleTime);
CREATE INDEX idx_checkin_room_status ON CheckIn(RoomId, OrderStatus);

-- Checkout 表
CREATE INDEX idx_checkout_customer_time ON Checkout(CustomerId, CheckoutTime);
CREATE INDEX idx_checkout_cashier_time ON Checkout(CashierId, CheckoutTime);

-- OperationLog 表
CREATE INDEX idx_operation_operator_time ON OperationLog(OperatorId, OperationTime);
CREATE INDEX idx_operation_type_time ON OperationLog(OperationTypeId, OperationTime);

-- CleaningTask 表
CREATE INDEX idx_cleaning_status_deadline ON CleaningTask(CleanStatus, DeadlineTime);
CREATE INDEX idx_cleaning_room_status ON CleaningTask(RoomId, CleanStatus);
CREATE INDEX idx_cleaning_cleaner_status ON CleaningTask(CleanerId, CleanStatus);
CREATE INDEX idx_cleaning_room_status ON CleaningTask(RoomId, CleanStatus);