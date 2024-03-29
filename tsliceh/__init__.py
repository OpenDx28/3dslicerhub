import datetime
import os
import uuid

from sqlalchemy import Column, JSON, Boolean, String, DateTime, TypeDecorator, CHAR
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class Base(object):
    pass


SQLAlchemyBase = declarative_base(cls=Base)


class Session3DSlicer(SQLAlchemyBase):
    __tablename__ = "sessions"
    uuid = Column(GUID, nullable=False, primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.datetime.now())
    last_activity = Column(DateTime, nullable=True)
    user = Column(String(64), unique=True, nullable=False)
    url_path = Column(String(1024), nullable=True)
    service_address = Column(String(1024), nullable=True)
    container_name = Column(String(128), nullable=True)
    restart = Column(Boolean, nullable=False, default=False)
    gpu = Column(Boolean, nullable=False, default=False)
    info = Column(JSON)


def create_local_orm(conn_str):
    from sqlalchemy import create_engine
    return create_engine(conn_str, echo=True, connect_args={"check_same_thread": False})


def create_session_factory(engine_):
    """ Return a session factory for a given engine """
    return scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine_))


def create_tables(engine_, declarative_base_=SQLAlchemyBase):
    """ Create tables of a declarative base using an engine """
    tables = declarative_base_.metadata.tables
    connection = engine_.connect()
    table_existence = [engine_.dialect.has_table(connection, tables[t].name) for t in tables]
    connection.close()
    if False in table_existence:
        declarative_base_.metadata.bind = engine_
        declarative_base_.metadata.create_all()


def get_ldap_address(mode, openldap_name, net_id):
    if mode == "container":
        from tsliceh.orchestrators import get_container_ip
        ldap_adress = get_container_ip(openldap_name, net_id) + ":389"
    else:
        ldap_adress = "localhost:389"
    return ldap_adress


def get_domain_name(mode, domain_name, port=None):
    from dotenv import load_dotenv
    if mode == "local":
        return domain_name + f":{port if port is not None else 8000}"
    else:
        externalIP  = os.popen('curl -s ifconfig.me').readline()
        print(externalIP)
        load_dotenv()
        if externalIP == os.getenv("IP"):
            return os.getenv("DOMAIN")
        else:
            return "localhost"


# def connect_ldap_server(ldap_adress):
#     """
#     https://medium.com/analytics-vidhya/crud-operations-for-openldap-using-python-ldap3-46393e3122af
#     :param ldap_adress:
#     :return:
#     """
#     try:
#
#         # Provide the hostname and port number of the openLDAP
#         # TODO FIND ldap ip
#         server_uri = ldap_adress
#         server = Server(server_uri, get_info=ALL)
#         # username and password can be configured during openldap setup
#         connection = Connection(server,
#                                 user='cn=admin,dc=opendx,dc=org',
#                                 password="admin_pass")
#         bind_response = connection.bind()  # Returns True or False
#     except LDAPBindError as e:
#         connection = e
#         return connection
#
#
# #
# # # For groups provide a groupid number instead of a uidNumber
# def get_ldap_users(ldap_adress):
#     """
#     https://medium.com/analytics-vidhya/crud-operations-for-openldap-using-python-ldap3-46393e3122af
#     :return:
#     :ldap_adress: interal IP of the container
#     """
#     # Provide a search base to search for.
#     search_base = 'dc=testldap,dc=com'
#     # provide a uidNumber to search for. '*" to fetch all users/groups
#     search_filter = '(uidNumber=500)'
#
#     # Establish connection to the server
#     ldap_conn = connect_ldap_server(ldap_adress)
#     try:
#         # only the attributes specified will be returned
#         ldap_conn.searchsearch('dc=opendx,dc=org', '(uid=*)',
#                                attributes=['sn', 'cn', 'homeDirectory'],
#                                size_limit=0)
#         # search will not return any values.
#         # the entries method in connection object returns the results
#         results = ldap_conn.entries
#     except LDAPException as e:
#         results = e


