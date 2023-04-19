import logging

chat_log = logging.getLogger('app.chat')

logging.basicConfig(
    filename = "chat_server.log",
    format = "%(asctime)s %(levelname)s %(filename)s %(message)s",
    level = logging.NOTSET
)

if __name__ == '__main__':
    chat_log.critical('Critical error')
    chat_log.error('Error!!!')
    chat_log.warning('Warning! Warning!')
    chat_log.debug('Information about debuggging')
    chat_log.info('Important info')