"""
Copyright (c) 2016-2018 Keith Sterling http://www.keithsterling.com

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import logging
from programy.utils.logging.ylogger import YLogger

import time
import hashlib
from datetime import datetime
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_ALL
from apscheduler.events import SchedulerEvent, JobEvent, JobSubmissionEvent, JobExecutionEvent


def scheduled(name, userid, clientid, action, text):
    ProgramyScheduler.scheduled_event(name, userid, clientid, action, text)


def scheduler_listener(event):
    ProgramyScheduler.listener_event(event)


class ProgramyScheduler(object):

    schedulers = {}

    def __init__(self, client, configuration):
        self._client = client

        self._configuration = configuration

        if self._configuration.debug_level is not None:
            self.set_debug_level(self._configuration.debug_level)

        self._scheduler = self._create_scheduler()

        self.register_schedulder(self, self._configuration.name)

        if self._configuration.add_listeners is True:
            self.register_listeners()

        if self._configuration.remove_all_jobs is True:
            self._scheduler.remove_all_jobs()

    @property
    def name(self):
        return self._configuration.name

    def register_schedulder(self, scheduler, name):
        if name in ProgramyScheduler.schedulers:
            YLogger.error(None, "Scheduler with name [%s] already registered", name)
        else:
            ProgramyScheduler.schedulers[name] = scheduler
            
    def set_debug_level(self, level):
        logging.getLogger('apscheduler').setLevel(level)

    def register_listeners(self):
        self._scheduler.add_listener(scheduler_listener, EVENT_ALL)

    def _create_scheduler(self):
        if self._configuration is not None:
            config = self._configuration.create_scheduler_config()
            if self._configuration.blocking is True:
                if config is not None:
                    YLogger.debug(None, "Creating Blocking Scheduler WITH config")
                    return BlockingScheduler(config)
                else:
                    YLogger.debug(None, "Creating Blocking Scheduler WITHOUT config")
                    return BlockingScheduler()
            else:
                if config is not None:
                    YLogger.debug(None, "Creating Background Scheduler WITH config")
                    return BackgroundScheduler(config)

        YLogger.debug(None, "Creating Background Scheduler WITHOUT config")
        return BackgroundScheduler()

    def start(self):
        self._scheduler.start()

    def stop(self):
        self._scheduler.shutdown()

    def wait_loop(self, period=5):
        try:
            while True:
                time.sleep(period)
        except:
            print("Shutting down...")
        finally:
            self.stop()

    def list_jobs(self):
        id_jobs = {}
        jobs = self._scheduler.get_jobs()
        for job in jobs:
            id_jobs[job.id] = job
        return id_jobs

    def create_job_id(self, userid, clientid, action, text):
        str = "%s:%s:%s:%s"%(userid, clientid, action, text)
        hashed = hashlib.md5(str.encode())
        return hashed.hexdigest()

    def remove_existing_jobs(self, job_id):
        old_job = self._scheduler.get_job(job_id)
        if old_job is not None:
            self._scheduler.remove_job(old_job)

    #################################################################################################################
    # Interval triggers

    def schedule_every_n_seconds(self, userid, clientid, action, text, seconds):
        job_id = self.create_job_id(userid, clientid, action, text)
        self.remove_existing_jobs(job_id)
        self._scheduler.add_job(scheduled, 'interval', [self.name, userid, clientid, action, text], id=job_id, seconds=seconds)

    def schedule_every_n_minutes(self, userid, clientid, action, text, minutes):
        job_id = self.create_job_id(userid, clientid, action, text)
        self.remove_existing_jobs(job_id)
        self._scheduler.add_job(scheduled, 'interval', [self.name, userid, clientid, action, text], id=job_id, minutes=minutes)

    def schedule_every_n_hours(self, userid, clientid, action, text, hours):
        job_id = self.create_job_id(userid, clientid, action, text)
        self.remove_existing_jobs(job_id)
        self._scheduler.add_job(scheduled, 'interval', [self.name, userid, clientid, action, text], id=job_id, hours=hours)

    def schedule_every_n_days(self, userid, clientid, action, text, days):
        job_id = self.create_job_id(userid, clientid, action, text)
        self.remove_existing_jobs(job_id)
        self._scheduler.add_job(scheduled, 'interval', [self.name, userid, clientid, action, text], id=job_id, days=days)

    def schedule_every_n_weeks(self, userid, clientid, action, text, weeks):
        job_id = self.create_job_id(userid, clientid, action, text)
        self.remove_existing_jobs(job_id)
        self._scheduler.add_job(scheduled, 'interval', [self.name, userid, clientid, action, text], id=job_id, weeks=weeks)

    def schedule_every_n(self, userid, clientid, action, text, weeks=0, days=0, hours=0, minutes=0, seconds=0):
        job_id = self.create_job_id(userid, clientid, action, text)
        self.remove_existing_jobs(job_id)
        self._scheduler.add_job(scheduled, 'interval', [self.name, userid, clientid, action, text], id=job_id, weeks=weeks, days=days,
                                hours=hours, minutes=minutes, seconds=seconds)

    #################################################################################################################
    # Date trigger

    def schedule_in_n_weeks(self, userid, clientid, action, text, weeks):
        now = datetime.now()
        the_future = now + timedelta(weeks=weeks)
        self.schedule_at_datetime(userid, clientid, action, text, the_future)

    def schedule_in_n_days(self, userid, clientid, action, text, days):
        now = datetime.now()
        the_future = now + timedelta(days=days)
        self.schedule_at_datetime(userid, clientid, action, text, the_future)

    def schedule_in_n_hours(self, userid, clientid, action, text, hours):
        now = datetime.now()
        the_future = now + timedelta(hours=hours)
        self.schedule_at_datetime(userid, clientid, action, text, the_future)

    def schedule_in_n_minutes(self, userid, clientid, action, text, minutes):
        now = datetime.now()
        the_future = now + timedelta(minutes=minutes)
        self.schedule_at_datetime(userid, clientid, action, text, the_future)

    def schedule_in_n_seconds(self, userid, clientid, action, text, seconds):
        now = datetime.now()
        the_future = now + timedelta(seconds=seconds)
        self.schedule_at_datetime(userid, clientid, action, text, the_future)

    def schedule_at_datetime(self, userid, clientid, action, text, schedule):
        job_id = self.create_job_id(userid, clientid, action, text)
        self.remove_existing_jobs(job_id)
        self._scheduler.add_job(scheduled, 'date', [self.name, userid, clientid, action, text], id=job_id, run_date=schedule)

    #################################################################################################################
    # Cron triggers

    def schedule_as_cron(self, userid, clientid, action, text, year='*', month='*', day='*', week='*', day_of_week='*',
                         hour='*', minute='*', second='*'):
        job_id = self.create_job_id(userid, clientid, action, text)
        self.remove_existing_jobs(job_id)
        self._scheduler.add_job(scheduled, 'cron', [self.name, userid, clientid, action, text], id=job_id, year=year, month=month, day=day,
                                week=week, day_of_week=day_of_week, hour=hour, minute=minute, second=second)


    #################################################################################################################
    # Admin/Debug Functions

    @staticmethod
    def get_event_str(event):
        if isinstance(event, JobExecutionEvent):
            if event.exception:
                return "JobExecutionEvent [%s] [%s] [%s] [%s] [%s] [%s]" % (
                event.code, event.job_id, event.jobstore, event.scheduled_run_time, event.retval, event.exception)
            else:
                return "JobExecutionEvent [%s] [%s] [%s] [%s] [%s]" % (
                event.code, event.job_id, event.jobstore, event.scheduled_run_time, event.retval)

        elif isinstance(event, JobSubmissionEvent):
            return "JobSubmissionEvent [%s] [%s] [%s] [%s]" % (
                    str(event.code), event.job_id, event.jobstore, event.scheduled_run_times)

        elif isinstance(event, JobEvent):
            return "JobEvent [%s] [%s] [%s] [%s]" % (event.code, event.job_id, event.jobstore, event.alias)

        elif isinstance(event, SchedulerEvent):
            return "SchedulerEvent [%s] [%s]" % (event.code, event.alias)

        return None

    @staticmethod
    def listener_event(event):
        try:
            message = ProgramyScheduler.get_event_str(event)
            if message is not None:
                YLogger.debug(None, message)
            else:
                YLogger.error(None, "Unknown APSchedulerEvent! %s", str(event))

        except Exception as e:
            YLogger.exception(None, "APScheduler Listener Error: %s", e)

    #################################################################################################################
    # Admin/Debug Functions

    @staticmethod
    def scheduled_event(name, userid, clientid, action, text):
        YLogger.debug(None, "Received Scheduled Event [%s] [%s] [%s] [%s] [%s]", name, userid, clientid, action, text)

        if name in ProgramyScheduler.schedulers:
            scheduler = ProgramyScheduler.schedulers[name]
            scheduler.scheduled(userid, clientid, action, text)
        else:
            YLogger.error(None, "Unknown scheduler [%s]", name)

    def scheduled(self, userid, clientid, action, text):
        YLogger.debug(None, "Processing Scheduled Event [%s] [%s] [%s] [%s] [%s]", self.name, userid, clientid, action, text)

        client_context = self._client.create_client_context(userid)
        if action == 'MESSAGE':
            self._client.render_response(client_context, text)
        elif action == 'GRAMMAR':
            response = client_context.bot.ask_question(client_context, text)
            self._client.render_response(client_context, response)
        else:
            YLogger.error(client_context, "Unknown scheduler command [%s]", action)
