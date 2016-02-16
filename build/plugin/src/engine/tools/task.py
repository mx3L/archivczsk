'''
Created on 10.9.2012

@author: marko
'''

from threading import Thread
from twisted.internet import defer
from twisted.python import log, failure
from Queue import Queue

from enigma import ePythonMessagePump
from Plugins.Extensions.archivCZSK import log
from Plugins.Extensions.archivCZSK.compat import eConnectCallback
from Plugins.Extensions.archivCZSK.engine.exceptions.addon import AddonThreadException
        
# object for stopping workerThread        
WorkerStop = object()

# queue for function to be executed in workerThread
fnc_queue = Queue(1)

# input queue to send results from reactor thread to running function in workerThread
fnc_in_queue = Queue(1)

#output queue to send function decorated by callFromThread from workerThread to reactor thread and run it there
fnc_out_queue = Queue(1)

def run_in_main_thread(val):
    #print 'run_in_main_thread -', currentThread().getName()
    fnc_out_queue.get()()
    
m_pump = None
m_pump_conn = None

def callFromThread(func):
    """calls function from child thread in main(reactor) thread, 
        and wait(in child thread) for result. Used mainly for GUI calls
        """
    def wrapped(*args, **kwargs):
        
        def _callFromThread():
            result = defer.maybeDeferred(func, *args, **kwargs)
            result.addBoth(fnc_in_queue.put)
        
        fnc_out_queue.put(_callFromThread)
        m_pump.send(0)
        result = fnc_in_queue.get()
        log.debug("result is %s" % str(result))
        if isinstance(result, failure.Failure):
            result.raiseException()
        return result
    return wrapped



class WorkerThread(Thread):
    
    def __init__(self):
        Thread.__init__(self)
        self.name = "ArchivCZSK-workerThread"

    def run(self):
        o = fnc_queue.get()
        while o is not WorkerStop:
            function, args, kwargs, onResult = o
            del o
            try:
                result = function(*args, **kwargs)
                success = True
            except:
                success = False
                result = failure.Failure()
            del function, args, kwargs
            try:
                onResult(success, result)
            except:
                log.err()
            del onResult, result
            o = fnc_queue.get()
        log.debug("worker thread stopped")
            
    def stop(self):
        log.debug("stopping working thread")
        fnc_queue.put(WorkerStop)


class Task(object):
    """Class for running single python task 
        at time in worker thread"""
        
    instance = None
    worker_thread = None
    
    @staticmethod
    def getInstance():
        return Task.instance
    
    @staticmethod
    def startWorkerThread():
        log.debug("[Task] starting workerThread")
        global m_pump_conn
        if m_pump_conn is not None:
            del m_pump_conn
        global m_pump
        if m_pump is None:
            m_pump = ePythonMessagePump()
        m_pump_conn = eConnectCallback(m_pump.recv_msg, run_in_main_thread)
        Task.worker_thread = WorkerThread()
        Task.worker_thread.start()
        
    @staticmethod   
    def stopWorkerThread():
        log.debug("[Task] stopping workerThread")
        Task.worker_thread.stop()
        Task.worker_thread.join()
        Task.worker_thread = None
        global m_pump_conn
        if m_pump_conn is not None:
            del m_pump_conn
        m_pump_conn = None
        global m_pump
        if m_pump is not None:
            m_pump.stop()
        m_pump = None
        
    @staticmethod     
    def setPollingInterval(self, interval):
        self.polling_interval = interval
        
    
    def __init__(self, callback, fnc, *args, **kwargs):
        log.debug('[Task] initializing')
        Task.instance = self
        self.callback = callback
        self.fnc = fnc
        self.args = args
        self.kwargs = kwargs
        self._running = False
        self._aborted = False
          
    def run(self):
        log.debug('[Task] running')
        self._running = True
        self._aborted = False
        
        o = (self.fnc, self.args, self.kwargs, self.onComplete)
        fnc_queue.put(o)
        
        
    def setResume(self):
        log.debug("[Task] resuming")
        self._aborted = False
    
    def setCancel(self):
        """ setting flag to abort executing compatible task
             (ie. controlling this flag in task execution) """
             
        log.debug('[Task] cancelling...')
        self._aborted = True
            
    def isCancelling(self):
        return self._aborted

    def onComplete(self, success, result):
        def wrapped_finish():
            Task.instance = None
            self.callback(success, result)
        
        if success:
            log.debug('[Task] completed with success')
        else:
            log.debug('[Task] completed with failure')
            
        # To make sure that, when we abort processing of task,
        # that its always the same type of failure
        if self._aborted:
            success = False
            result = failure.Failure(AddonThreadException())
        fnc_out_queue.put(wrapped_finish)
        m_pump.send(0)
