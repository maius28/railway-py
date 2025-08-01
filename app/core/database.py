import os
import pymysql
from typing import Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """数据库配置管理类"""
    
    @staticmethod
    def get_db_config() -> Dict[str, str]:
        """获取数据库配置，优先从环境变量读取"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'qwe123'),
            'database': os.getenv('DB_NAME', 'train'),
            'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
            'autocommit': True,
            'connect_timeout': 60,
            'read_timeout': 30,
            'write_timeout': 30
        }

class DatabaseConnection:
    """数据库连接管理类"""
    
    def __init__(self, max_retries: int = 5, retry_delay: int = 5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.db = None
        self.cursor = None
        
    def connect(self) -> bool:
        """建立数据库连接，支持重试机制"""
        config = DatabaseConfig.get_db_config()
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"尝试连接数据库 (第 {attempt + 1} 次): {config['host']}:{config['port']}")
                
                self.db = pymysql.connect(**config)
                self.cursor = self.db.cursor()
                
                # 测试连接
                self.cursor.execute("SELECT 1")
                self.cursor.fetchone()
                
                logger.info("数据库连接成功")
                return True
                
            except Exception as e:
                logger.error(f"数据库连接失败 (第 {attempt + 1} 次): {e}")
                
                if attempt < self.max_retries - 1:
                    logger.info(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error("数据库连接失败，已达到最大重试次数")
                    
        return False
    
    def is_connected(self) -> bool:
        """检查数据库连接是否有效"""
        try:
            if self.db and self.cursor:
                self.cursor.execute("SELECT 1")
                return True
        except:
            pass
        return False
    
    def reconnect(self) -> bool:
        """重新连接数据库"""
        self.close()
        return self.connect()
    
    def close(self):
        """关闭数据库连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.db:
                self.db.close()
        except:
            pass
        finally:
            self.cursor = None
            self.db = None
    
    def execute_with_retry(self, sql: str, params=None):
        """执行SQL语句，支持连接重试"""
        if not self.is_connected():
            if not self.reconnect():
                raise Exception("无法建立数据库连接")
        
        try:
            self.cursor.execute(sql, params)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"SQL执行失败: {e}")
            # 尝试重新连接一次
            if self.reconnect():
                self.cursor.execute(sql, params)
                return self.cursor.fetchall()
            else:
                raise e

# 全局数据库连接实例
db_connection = DatabaseConnection()
