
-- 折扣等级
INSERT INTO Discount(DiscountGrade, DiscountRate) VALUES
(0, 1.0000),
(1, 0.9500),
(2, 0.9000),
(3, 0.8500);

-- 账号权限
INSERT INTO AccountPermission(PermissionName, PermissionScope) VALUES
('管理员', '账号审核、客房管理、客户管理、预定管理、入住管理、结账管理、操作审计、清扫任务管理'),
('前台工作人员', '客户管理、预定管理、入住管理、结账管理、清扫任务查询'),
('保洁员', '清扫任务查询、清扫开始、清扫完成'),
('审计员', '操作记录查询、账单查询');

-- 操作类型
INSERT INTO OperationType(OperationTypeName) VALUES
('创建预定'),
('办理入住'),
('办理结账'),
('开始清扫'),
('完成清扫'),
('账号审核'),
('客房维护'),
('客户维护');

INSERT INTO OperationType(OperationTypeName) VALUES ('换房');