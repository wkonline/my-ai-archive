"""
API 后端模型层：直接复用 cono.models（与老版系统共享同一份数据库表）。
"""
from cono.models import *  # noqa: F401,F403
from cono.models import (
    ModelBase, Department, User, Customer, Warehouse,
    ProductCategory, Product, Contract, Contract_Product,
    Collection, Invoice, Service, ServiceDetail, ReturnProduct,
    Plan, ProductionTask, ContractFile, ProductLabel, ProductDelivery,
    Admin as MyCompany, UserLog, AuthRole, AuthUserProfile, TEMP_CONTRACT_NUMBER,
)
