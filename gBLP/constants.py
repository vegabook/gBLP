# constants for message types from the bbg terminal
RESP_INFO = "info"
RESP_REF = "refdata"
RESP_SUB = "subdata"
RESP_BAR = "bardata"
RESP_STATUS = "status"
RESP_ERROR = "error"
RESP_ACK = "ack"
DEFAULT_FIELDS = ["LAST_PRICE", "BLOOMBERG_SEND_TIME_RT", "BID", "ASK"]

MAX_MESSAGE_LENGTH = 20000000   # the maximum GRPC message length

PONG_SECONDS_TIMEOUT = 5 # the number of seconds to wait for a pong before disconnecting


#from bloomberg_pb2 import Topic
#
#topicTypeName = Topic.topicType.Name(topic.ttype) # SEDOL1/TICKER/CUSIP etc
#
#
#
#enum msgType {
#  UNKNOWN = 0;
#  INFO = 1;
#  REFDATA = 2;
#  SUBDATA = 3;
#  BARDATA = 4;
#  STATUS = 5;
#  ERROR = 6;
#  ACK = 7;
#}
#
#enum topicType {
#  TICKER = 0;
#  SEDOL1 = 1;
#  CUSIP = 2;
#}

