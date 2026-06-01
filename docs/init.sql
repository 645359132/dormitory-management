-- 学生宿舍管理系统 - SQL Server 初始化脚本
-- 适用于 SQL Server 2019+

IF DB_ID(N'DormMgmt') IS NOT NULL
BEGIN
    ALTER DATABASE DormMgmt SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE DormMgmt;
END
GO

CREATE DATABASE DormMgmt;
GO

USE DormMgmt;
GO

CREATE TABLE Dormitory (
    BuildingNo     NVARCHAR(10) NOT NULL,
    RoomNo         NVARCHAR(10) NOT NULL,
    BedTotal       INT          NOT NULL,
    BedUsed        INT          NOT NULL DEFAULT 0,
    HeadStudentId  CHAR(12)     NULL,
    CONSTRAINT PK_Dormitory PRIMARY KEY CLUSTERED (BuildingNo, RoomNo),
    CONSTRAINT CK_Dorm_BedTotal CHECK (BedTotal BETWEEN 1 AND 8),
    CONSTRAINT CK_Dorm_BedUsed CHECK (BedUsed >= 0 AND BedUsed <= BedTotal)
);
GO

CREATE TABLE Student (
    StudentId   CHAR(12)      NOT NULL,
    Name        NVARCHAR(20)  NOT NULL,
    Gender      NVARCHAR(2)   NOT NULL,
    Major       NVARCHAR(40)  NULL,
    [Class]     NVARCHAR(40)  NULL,
    Phone       CHAR(11)      NULL,
    BuildingNo  NVARCHAR(10)  NULL,
    RoomNo      NVARCHAR(10)  NULL,
    CONSTRAINT PK_Student PRIMARY KEY CLUSTERED (StudentId),
    CONSTRAINT CK_Student_Gender CHECK (Gender IN (N'男', N'女')),
    CONSTRAINT CK_Student_Phone CHECK (Phone IS NULL OR Phone LIKE '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
    CONSTRAINT FK_Student_Dorm FOREIGN KEY (BuildingNo, RoomNo)
        REFERENCES Dormitory(BuildingNo, RoomNo)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);
GO

ALTER TABLE Dormitory ADD CONSTRAINT FK_Dorm_Head
    FOREIGN KEY (HeadStudentId) REFERENCES Student(StudentId)
    ON DELETE NO ACTION;
GO

CREATE TABLE Admin (
    AdminId   VARCHAR(20)  NOT NULL,
    Password  VARCHAR(128) NOT NULL,
    Role      VARCHAR(10)  NOT NULL DEFAULT 'admin',
    CONSTRAINT PK_Admin PRIMARY KEY CLUSTERED (AdminId),
    CONSTRAINT CK_Admin_Role CHECK (Role IN ('admin', 'student'))
);
GO

CREATE TABLE UtilityBill (
    BillId        CHAR(16)      NOT NULL,
    BuildingNo    NVARCHAR(10)  NOT NULL,
    RoomNo        NVARCHAR(10)  NOT NULL,
    BillMonth     CHAR(7)       NOT NULL,
    WaterFee      DECIMAL(8,2)  NOT NULL DEFAULT 0,
    ElectricFee   DECIMAL(8,2)  NOT NULL DEFAULT 0,
    TotalAmount   DECIMAL(8,2)  NOT NULL DEFAULT 0,
    PayStatus     NVARCHAR(4)   NOT NULL DEFAULT N'未缴',
    CONSTRAINT PK_UtilityBill PRIMARY KEY CLUSTERED (BillId),
    CONSTRAINT FK_Bill_Dorm FOREIGN KEY (BuildingNo, RoomNo)
        REFERENCES Dormitory(BuildingNo, RoomNo),
    CONSTRAINT CK_Bill_Month CHECK (BillMonth LIKE '[0-9][0-9][0-9][0-9]-[0-1][0-9]'),
    CONSTRAINT CK_Bill_Water CHECK (WaterFee >= 0),
    CONSTRAINT CK_Bill_Elec CHECK (ElectricFee >= 0),
    CONSTRAINT CK_Bill_Status CHECK (PayStatus IN (N'已缴', N'未缴')),
    CONSTRAINT UQ_Bill_Room_Month UNIQUE (BuildingNo, RoomNo, BillMonth)
);
GO

CREATE TABLE RepairRecord (
    RepairId     CHAR(16)       NOT NULL,
    StudentId    CHAR(12)       NOT NULL,
    BuildingNo   NVARCHAR(10)   NOT NULL,
    RoomNo       NVARCHAR(10)   NOT NULL,
    RepairType   NVARCHAR(20)   NOT NULL,
    FaultDetail  NVARCHAR(200)  NULL,
    Worker       NVARCHAR(20)   NULL,
    Fee          DECIMAL(8,2)   NOT NULL DEFAULT 0,
    Status       NVARCHAR(10)   NOT NULL DEFAULT N'待处理',
    SubmitTime   DATETIME       NOT NULL DEFAULT GETDATE(),
    CONSTRAINT PK_RepairRecord PRIMARY KEY CLUSTERED (RepairId),
    CONSTRAINT FK_Repair_Student FOREIGN KEY (StudentId) REFERENCES Student(StudentId),
    CONSTRAINT FK_Repair_Dorm FOREIGN KEY (BuildingNo, RoomNo) REFERENCES Dormitory(BuildingNo, RoomNo),
    CONSTRAINT CK_Repair_Type CHECK (RepairType IN (N'水电', N'木工', N'门窗', N'其他')),
    CONSTRAINT CK_Repair_Status CHECK (Status IN (N'待处理', N'维修中', N'已完成')),
    CONSTRAINT CK_Repair_Fee CHECK (Fee >= 0)
);
GO

CREATE TABLE HygieneRecord (
    RecordId    INT IDENTITY(1,1) NOT NULL,
    BuildingNo  NVARCHAR(10)      NOT NULL,
    RoomNo      NVARCHAR(10)      NOT NULL,
    CheckDate   DATE              NOT NULL DEFAULT CONVERT(DATE, GETDATE()),
    Score       INT               NOT NULL,
    Result      NCHAR(1)          NULL,
    CONSTRAINT PK_HygieneRecord PRIMARY KEY CLUSTERED (RecordId),
    CONSTRAINT FK_Hygiene_Dorm FOREIGN KEY (BuildingNo, RoomNo)
        REFERENCES Dormitory(BuildingNo, RoomNo),
    CONSTRAINT CK_Hygiene_Score CHECK (Score BETWEEN 0 AND 100),
    CONSTRAINT CK_Hygiene_Result CHECK (Result IN (N'优', N'良', N'中', N'差'))
);
GO

CREATE TABLE ItemRecord (
    ItemId       CHAR(16)      NOT NULL,
    StudentId    CHAR(12)      NOT NULL,
    ItemName     NVARCHAR(50)  NOT NULL,
    Action       NVARCHAR(10)  NOT NULL,
    Quantity     INT           NOT NULL DEFAULT 1,
    Status       NVARCHAR(10)  NOT NULL DEFAULT N'已登记',
    RegisterTime DATETIME      NOT NULL DEFAULT GETDATE(),
    Remark       NVARCHAR(200) NULL,
    CONSTRAINT PK_ItemRecord PRIMARY KEY CLUSTERED (ItemId),
    CONSTRAINT FK_Item_Student FOREIGN KEY (StudentId) REFERENCES Student(StudentId),
    CONSTRAINT CK_Item_Action CHECK (Action IN (N'存入', N'取出')),
    CONSTRAINT CK_Item_Status CHECK (Status IN (N'已登记', N'已归还')),
    CONSTRAINT CK_Item_Quantity CHECK (Quantity > 0)
);
GO

CREATE TABLE VisitorRecord (
    VisitorId       CHAR(16)      NOT NULL,
    VisitorName     NVARCHAR(20)  NOT NULL,
    Phone           CHAR(11)      NULL,
    VisitStudentId  CHAR(12)      NOT NULL,
    BuildingNo      NVARCHAR(10)  NOT NULL,
    RoomNo          NVARCHAR(10)  NOT NULL,
    EnterTime       DATETIME      NOT NULL DEFAULT GETDATE(),
    LeaveTime       DATETIME      NULL,
    Status          NVARCHAR(10)  NOT NULL DEFAULT N'在访',
    Remark          NVARCHAR(200) NULL,
    CONSTRAINT PK_VisitorRecord PRIMARY KEY CLUSTERED (VisitorId),
    CONSTRAINT FK_Visitor_Student FOREIGN KEY (VisitStudentId) REFERENCES Student(StudentId),
    CONSTRAINT FK_Visitor_Dorm FOREIGN KEY (BuildingNo, RoomNo) REFERENCES Dormitory(BuildingNo, RoomNo),
    CONSTRAINT CK_Visitor_Phone CHECK (Phone IS NULL OR Phone LIKE '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
    CONSTRAINT CK_Visitor_Status CHECK (Status IN (N'在访', N'已离开'))
);
GO

CREATE TABLE RepairStatusLog (
    LogId      INT IDENTITY(1,1) PRIMARY KEY,
    RepairId   CHAR(16)     NOT NULL,
    OldStatus  NVARCHAR(10) NULL,
    NewStatus  NVARCHAR(10) NULL,
    ChangeTime DATETIME     NOT NULL DEFAULT GETDATE(),
    Operator   SYSNAME      NOT NULL DEFAULT SYSTEM_USER
);
GO

CREATE TABLE AuditLog (
    LogId      INT IDENTITY(1,1) PRIMARY KEY,
    OperatorId VARCHAR(20)   NULL,
    ActionType NVARCHAR(30)  NOT NULL,
    TargetId   NVARCHAR(30)  NULL,
    Detail     NVARCHAR(200) NULL,
    CreatedAt  DATETIME      NOT NULL DEFAULT GETDATE()
);
GO

CREATE NONCLUSTERED INDEX IDX_Student_Room ON Student(BuildingNo, RoomNo);
CREATE NONCLUSTERED INDEX IDX_Dormitory_Vacancy ON Dormitory(BedTotal, BedUsed);
CREATE NONCLUSTERED INDEX IDX_Bill_Status ON UtilityBill(PayStatus) INCLUDE (TotalAmount, BuildingNo, RoomNo);
CREATE NONCLUSTERED INDEX IDX_Repair_Student ON RepairRecord(StudentId);
CREATE NONCLUSTERED INDEX IDX_Repair_Status ON RepairRecord(Status);
CREATE NONCLUSTERED INDEX IDX_Hygiene_RoomDate ON HygieneRecord(BuildingNo, RoomNo, CheckDate DESC);
CREATE NONCLUSTERED INDEX IDX_Item_Student ON ItemRecord(StudentId, RegisterTime DESC);
CREATE NONCLUSTERED INDEX IDX_Visitor_Status ON VisitorRecord(Status, EnterTime DESC);
GO

CREATE OR ALTER VIEW vw_StudentDormitory AS
SELECT s.StudentId,
       s.Name,
       s.Gender,
       s.Major,
       s.[Class],
       s.Phone,
       s.BuildingNo,
       s.RoomNo,
       d.BedTotal,
       d.BedUsed,
       d.HeadStudentId
FROM Student AS s
LEFT JOIN Dormitory AS d
    ON s.BuildingNo = d.BuildingNo AND s.RoomNo = d.RoomNo;
GO

CREATE OR ALTER VIEW vw_UnpaidBills AS
SELECT b.BillId,
       b.BuildingNo,
       b.RoomNo,
       b.BillMonth,
       b.WaterFee,
       b.ElectricFee,
       b.TotalAmount,
       b.PayStatus,
       s.StudentId,
       s.Name AS StudentName
FROM UtilityBill AS b
LEFT JOIN Student AS s
    ON s.BuildingNo = b.BuildingNo AND s.RoomNo = b.RoomNo
WHERE b.PayStatus = N'未缴';
GO

CREATE OR ALTER VIEW vw_HygieneRanking AS
SELECT h.BuildingNo,
       h.RoomNo,
       AVG(CAST(h.Score AS FLOAT)) AS AvgScore,
       COUNT(*) AS CheckCount,
       MAX(h.CheckDate) AS LastCheckDate,
       RANK() OVER (ORDER BY AVG(CAST(h.Score AS FLOAT)) DESC) AS RankNo
FROM HygieneRecord AS h
GROUP BY h.BuildingNo, h.RoomNo;
GO

CREATE OR ALTER VIEW vw_RoomVacancy AS
SELECT BuildingNo,
       RoomNo,
       BedTotal,
       BedUsed,
       BedTotal - BedUsed AS VacantBeds
FROM Dormitory
WHERE BedUsed < BedTotal;
GO

CREATE OR ALTER TRIGGER trg_Student_BedUsed
ON Student
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE d
    SET d.BedUsed = ISNULL(s.UsedCount, 0)
    FROM Dormitory AS d
    LEFT JOIN (
        SELECT BuildingNo, RoomNo, COUNT(*) AS UsedCount
        FROM Student
        WHERE BuildingNo IS NOT NULL AND RoomNo IS NOT NULL
        GROUP BY BuildingNo, RoomNo
    ) AS s
        ON s.BuildingNo = d.BuildingNo AND s.RoomNo = d.RoomNo;

    IF EXISTS (SELECT 1 FROM Dormitory WHERE BedUsed > BedTotal)
    BEGIN
        RAISERROR(N'已住人数超过床位总数，操作回滚', 16, 1);
        ROLLBACK TRANSACTION;
    END
END;
GO

CREATE OR ALTER TRIGGER trg_UtilityBill_Total
ON UtilityBill
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE b
    SET TotalAmount = b.WaterFee + b.ElectricFee
    FROM UtilityBill AS b
    INNER JOIN inserted AS i ON i.BillId = b.BillId
    WHERE b.TotalAmount <> b.WaterFee + b.ElectricFee;
END;
GO

CREATE OR ALTER TRIGGER trg_HygieneRecord_Result
ON HygieneRecord
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE h
    SET Result = CASE
        WHEN i.Score >= 90 THEN N'优'
        WHEN i.Score >= 80 THEN N'良'
        WHEN i.Score >= 60 THEN N'中'
        ELSE N'差'
    END
    FROM HygieneRecord AS h
    INNER JOIN inserted AS i ON i.RecordId = h.RecordId;
END;
GO

CREATE OR ALTER TRIGGER trg_Repair_LogStatus
ON RepairRecord
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    IF UPDATE(Status)
    BEGIN
        INSERT INTO RepairStatusLog(RepairId, OldStatus, NewStatus)
        SELECT i.RepairId, d.Status, i.Status
        FROM inserted AS i
        INNER JOIN deleted AS d ON i.RepairId = d.RepairId
        WHERE ISNULL(i.Status, N'') <> ISNULL(d.Status, N'');
    END
END;
GO

CREATE OR ALTER TRIGGER trg_Bill_Audit
ON UtilityBill
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO AuditLog(OperatorId, ActionType, TargetId, Detail)
    SELECT SYSTEM_USER,
           N'账单修改',
           i.BillId,
           CONCAT(N'状态: ', d.PayStatus, N' -> ', i.PayStatus, N'; 金额: ', d.TotalAmount, N' -> ', i.TotalAmount)
    FROM inserted AS i
    INNER JOIN deleted AS d ON i.BillId = d.BillId
    WHERE i.PayStatus <> d.PayStatus
       OR i.WaterFee <> d.WaterFee
       OR i.ElectricFee <> d.ElectricFee;
END;
GO

CREATE OR ALTER PROCEDURE usp_AssignDormitory
    @StudentId  CHAR(12),
    @BuildingNo NVARCHAR(10),
    @RoomNo     NVARCHAR(10)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (SELECT 1 FROM Dormitory WHERE BuildingNo = @BuildingNo AND RoomNo = @RoomNo)
            THROW 50001, N'指定宿舍不存在', 1;

        IF (
            SELECT COUNT(*)
            FROM Student
            WHERE BuildingNo = @BuildingNo AND RoomNo = @RoomNo AND StudentId <> @StudentId
        ) >= (
            SELECT BedTotal
            FROM Dormitory
            WHERE BuildingNo = @BuildingNo AND RoomNo = @RoomNo
        )
            THROW 50002, N'该房间已住满', 1;

        UPDATE Student
        SET BuildingNo = @BuildingNo, RoomNo = @RoomNo
        WHERE StudentId = @StudentId;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

CREATE OR ALTER PROCEDURE usp_GenerateUtilityBill
    @BuildingNo  NVARCHAR(10),
    @RoomNo      NVARCHAR(10),
    @BillMonth   CHAR(7),
    @WaterFee    DECIMAL(8,2),
    @ElectricFee DECIMAL(8,2)
AS
BEGIN
    SET NOCOUNT ON;

    IF NOT EXISTS (SELECT 1 FROM Dormitory WHERE BuildingNo = @BuildingNo AND RoomNo = @RoomNo)
        THROW 50010, N'宿舍不存在', 1;

    DECLARE @BillId CHAR(16) =
        'B' + CONVERT(CHAR(8), GETDATE(), 112)
        + RIGHT('0000000' + CAST(ABS(CHECKSUM(NEWID())) % 10000000 AS VARCHAR(7)), 7);

    INSERT INTO UtilityBill(BillId, BuildingNo, RoomNo, BillMonth, WaterFee, ElectricFee, TotalAmount, PayStatus)
    VALUES (@BillId, @BuildingNo, @RoomNo, @BillMonth, @WaterFee, @ElectricFee, @WaterFee + @ElectricFee, N'未缴');

    SELECT @BillId AS NewBillId;
END;
GO

CREATE OR ALTER PROCEDURE usp_PayBill
    @BillId CHAR(16),
    @PayAmount DECIMAL(8,2)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @Total DECIMAL(8,2), @PayStatus NVARCHAR(4);
        SELECT @Total = TotalAmount, @PayStatus = PayStatus
        FROM UtilityBill WITH (UPDLOCK, ROWLOCK)
        WHERE BillId = @BillId;

        IF @Total IS NULL THROW 50020, N'账单不存在', 1;
        IF @PayStatus = N'已缴' THROW 50021, N'账单已缴清', 1;
        IF @PayAmount < @Total THROW 50022, N'缴费金额不足', 1;

        UPDATE UtilityBill
        SET PayStatus = N'已缴'
        WHERE BillId = @BillId;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

CREATE OR ALTER PROCEDURE usp_SubmitRepair
    @StudentId   CHAR(12),
    @RepairType  NVARCHAR(20),
    @FaultDetail NVARCHAR(200)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @BuildingNo NVARCHAR(10), @RoomNo NVARCHAR(10);
    SELECT @BuildingNo = BuildingNo, @RoomNo = RoomNo
    FROM Student
    WHERE StudentId = @StudentId;

    IF @BuildingNo IS NULL OR @RoomNo IS NULL
        THROW 50030, N'学生未入住任何宿舍', 1;

    DECLARE @RepairId CHAR(16) =
        'R' + CONVERT(CHAR(8), GETDATE(), 112)
        + RIGHT('0000000' + CAST(ABS(CHECKSUM(NEWID())) % 10000000 AS VARCHAR(7)), 7);

    INSERT INTO RepairRecord(RepairId, StudentId, BuildingNo, RoomNo, RepairType, FaultDetail, Status, Fee)
    VALUES (@RepairId, @StudentId, @BuildingNo, @RoomNo, @RepairType, @FaultDetail, N'待处理', 0);

    SELECT @RepairId AS NewRepairId;
END;
GO

CREATE OR ALTER PROCEDURE usp_RecordHygiene
    @BuildingNo NVARCHAR(10),
    @RoomNo     NVARCHAR(10),
    @Score      INT,
    @CheckDate  DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;

    IF @CheckDate IS NULL SET @CheckDate = CONVERT(DATE, GETDATE());

    INSERT INTO HygieneRecord(BuildingNo, RoomNo, Score, CheckDate)
    VALUES (@BuildingNo, @RoomNo, @Score, @CheckDate);
END;
GO

INSERT INTO Dormitory(BuildingNo, RoomNo, BedTotal)
VALUES
    (N'八楼南', N'401', 4),
    (N'八楼南', N'402', 4),
    (N'十八楼北', N'501', 6),
    (N'十八楼北', N'502', 6);
GO

INSERT INTO Student(StudentId, Name, Gender, Major, [Class], Phone, BuildingNo, RoomNo)
VALUES
    ('24050710', N'张三', N'男', N'软件工程', N'软工2401', '13800000001', N'八楼南', N'401'),
    ('24050711', N'李四', N'男', N'软件工程', N'软工2401', '13800000002', N'八楼南', N'401'),
    ('24050712', N'王五', N'女', N'计算机科学与技术', N'计科2402', '13800000003', N'十八楼北', N'501'),
    ('24050713', N'赵六', N'女', N'计算机科学与技术', N'计科2402', '13800000004', N'十八楼北', N'501');
GO

UPDATE Dormitory SET HeadStudentId = '24050710' WHERE BuildingNo = N'八楼南' AND RoomNo = N'401';
GO

INSERT INTO Admin(AdminId, Password, Role)
VALUES
    ('admin01', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin'),
    ('24050710', '24050710', 'student'),
    ('24050711', '24050711', 'student'),
    ('24050712', '24050712', 'student'),
    ('24050713', '24050713', 'student');
GO

INSERT INTO UtilityBill(BillId, BuildingNo, RoomNo, BillMonth, WaterFee, ElectricFee, TotalAmount, PayStatus)
VALUES
    ('B20260501000001', N'八楼南', N'401', '2026-05', 35.50, 78.20, 113.70, N'未缴'),
    ('B20260501000002', N'十八楼北', N'501', '2026-05', 42.00, 88.60, 130.60, N'已缴');
GO

INSERT INTO RepairRecord(RepairId, StudentId, BuildingNo, RoomNo, RepairType, FaultDetail, Worker, Fee, Status)
VALUES
    ('R20260501000001', '24050710', N'八楼南', N'401', N'水电', N'卫生间水龙头漏水', NULL, 0, N'待处理'),
    ('R20260501000002', '24050712', N'十八楼北', N'501', N'门窗', N'阳台门锁损坏', N'王师傅', 25.00, N'已完成');
GO

INSERT INTO HygieneRecord(BuildingNo, RoomNo, CheckDate, Score)
VALUES
    (N'八楼南', N'401', '2026-05-20', 92),
    (N'十八楼北', N'501', '2026-05-20', 84),
    (N'八楼南', N'402', '2026-05-20', 76);
GO
