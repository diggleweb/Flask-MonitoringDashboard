"""
Contains all functions that access a single endpoint
"""
import datetime
from collections import defaultdict

from sqlalchemy import func, desc
from sqlalchemy.orm.exc import NoResultFound

from flask_monitoringdashboard.core.timezone import to_local_datetime
from flask_monitoringdashboard.database import Request, Endpoint


def get_num_requests(db_session, endpoint_id, start_date, end_date):
    """ Returns a list with all dates on which an endpoint is accessed.
        :param db_session: session containing the query
        :param endpoint_id: if None, the result is the sum of all endpoints
        :param start_date: datetime.date object
        :param end_date: datetime.date object
    """
    query = db_session.query(Request.time_requested)
    if endpoint_id:
        query = query.filter(Request.endpoint_id == endpoint_id)
    result = query.filter(Request.time_requested >= start_date, Request.duration <= end_date).all()

    return group_execution_times([r[0] for r in result])


def group_execution_times(datetimes):
    """
    Returns a list of tuples containing the number of hits per hour
    :param datetimes: list of datetime objects
    :return: list of tuples ('%Y-%m-%d %H:00:00', count)
    """
    hours_dict = defaultdict(int)
    for dt in datetimes:
        round_time = dt.strftime('%Y-%m-%d %H:00:00')
        hours_dict[round_time] += 1
    return hours_dict.items()


def get_users(db_session, endpoint_id, limit=None):
    """
    Returns a list with the distinct group-by from a specific endpoint. The limit is used to filter the most used
    distinct.
    :param db_session: session containing the query
    :param endpoint_id: the endpoint_id to filter on
    :param limit: the number of
    :return: a list with the group_by as strings.
    """
    query = db_session.query(Request.group_by, func.count(Request.group_by)). \
        filter(Request.endpoint_id == endpoint_id).group_by(Request.group_by). \
        order_by(desc(func.count(Request.group_by)))
    if limit:
        query = query.limit(limit)
    result = query.all()
    db_session.expunge_all()
    return [r[0] for r in result]


def get_ips(db_session, endpoint_id, limit=None):
    """
    Returns a list with the distinct group-by from a specific endpoint. The limit is used to filter the most used
    distinct.
    :param db_session: session containing the query
    :param endpoint_id: the endpoint_id to filter on
    :param limit: the number of
    :return: a list with the group_by as strings.
    """
    query = db_session.query(Request.ip, func.count(Request.ip)). \
        filter(Request.endpoint_id == endpoint_id).group_by(Request.ip). \
        order_by(desc(func.count(Request.ip)))
    if limit:
        query = query.limit(limit)
    result = query.all()
    db_session.expunge_all()
    return [r[0] for r in result]


def get_endpoint_by_name(db_session, endpoint_name):
    """get the Endpoint-object from a given endpoint_name.
    If the result doesn't exist in the database, a new row is added.
    :param db_session: session for the database
    :param endpoint_name: string with the endpoint name. """
    try:
        result = db_session.query(Endpoint). \
            filter(Endpoint.name == endpoint_name).one()
        result.time_added = to_local_datetime(result.time_added)
        result.last_requested = to_local_datetime(result.last_requested)
    except NoResultFound:
        result = Endpoint(name=endpoint_name)
        db_session.add(result)
        db_session.flush()
    db_session.expunge(result)
    return result


def get_endpoint_by_id(db_session, id):
    """
    get the Endpoint-object from a given endpoint_id.
    :param db_session: session for the database
    :param id: id of the endpoint.
    """
    result = db_session.query(Endpoint).filter(Endpoint.id == id).one()
    db_session.expunge(result)
    return result


def update_endpoint(db_session, endpoint_name, value):
    """ Update the value of a specific monitor rule. """
    db_session.query(Endpoint).filter(Endpoint.name == endpoint_name). \
        update({Endpoint.monitor_level: value})
    db_session.flush()


def get_last_requested(db_session):
    """ Returns the accessed time of a single endpoint. """
    result = db_session.query(Endpoint.name, Endpoint.last_requested).all()
    db_session.expunge_all()
    return [(end, to_local_datetime(time)) for end, time in result]


def update_last_accessed(db_session, endpoint_name):
    """ Updates the timestamp of last access of the endpoint. """
    db_session.query(Endpoint).filter(Endpoint.name == endpoint_name). \
        update({Endpoint.last_requested: datetime.datetime.utcnow()})


def get_endpoints(db_session):
    """ Returns the name of all endpoints from the database """
    return db_session.query(Endpoint).all()


def get_endpoint_data(db_session):
    """
    Returns all data in the endpoints table. This table contains which endpoints are being
    monitored and which are not.
    :return: all data from the database in the rules-table.
    """
    result = db_session.query(Endpoint).all()
    db_session.expunge_all()
    return result
