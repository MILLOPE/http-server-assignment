import logging

# 配置日志记录，将日志级别设置为 INFO
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 创建一个 logger 对象
logger = logging.getLogger(__name__)

# 使用 logger.debug 输出调试信息
logger.debug('ssss')

# 使用 logger.info 输出一般信息
logger.info('info')