#tests for appObj
from TestHelperSuperClass import testHelperAPIClient
from jobsDataAPI import jobClass
from JobExecution import JobExecutionClass
from appObj import appObj
import time
from utils import from_iso8601

class test_JobExecution(testHelperAPIClient):

  def test_Create(self):
    jobObj = jobClass('TestJob123', 'echo "This is a test"', True, '')
    a = JobExecutionClass(jobObj)
    tim = from_iso8601(a.dateCreated)
    self.assertTimeCloseToCurrent(tim)
    self.assertEqual(a.stage, 'Pending')
    self.assertEqual(a.jobGUID, jobObj.guid)
    self.assertEqual(a.jobCommand, jobObj.command)

  def test_run(self):
    jobObj = jobClass('TestJob123', 'echo "This is a test"', True, '')
    a = JobExecutionClass(jobObj)
    a.execute(appObj.jobExecutor)
    self.assertEqual(a.stage, 'Completed')
    self.assertEqual(a.resultReturnCode, 0)
    self.assertEqual(a.resultSTDOUT, 'This is a test')

  #Time consuming tests commented out
  #def test_timeout(self):
  #  jobObj = jobClass('TestJob123', 'sleep 5', True, '')
  #  a = JobExecutionClass(jobObj)
  #  appObj.jobExecutor.timeout = 1
  #  start_time = time.time()
  #  a.execute(appObj.jobExecutor)
  #  elapsed_time = time.time() - start_time
  #  self.assertLess(elapsed_time, 2)
  #  self.assertEqual(a.stage, 'Timeout')
  #  self.assertEqual(a.resultReturnCode, -1)

  #I don't have this test working yet
  #def test_bigoutput(self):
  #  jobObj = jobClass('TestJob123', 'find /', True, '')
  #  a = JobExecutionClass(jobObj)
  #  appObj.jobExecutor.timeout = 1 #Increase
  #  a.execute(appObj.jobExecutor)
  #  self.assertEqual(a.stage, 'Completed')
  #  self.assertEqual(a.resultReturnCode, 0)

  def test_dictOut(self):
    jobObj = jobClass('TestJob123', 'echo "This is a test"', True, '')
    expPending = {
      'guid': 'OVERRIDE',
      'stage': 'Pending',
      'jobGUID': jobObj.guid,
      'jobCommand': jobObj.command,
      'dateCreated': 'OVERRIDE',
      'dateStarted': None,
      'dateCompleted': None,
      'resultReturnCode': None,
      'resultSTDOUT': None
    }
    expCompleted = dict(expPending)
    expCompleted['resultSTDOUT'] = 'This is a test'
    expCompleted['stage'] = 'Completed'
    expCompleted['dateStarted'] = 'OVERRIDE'
    expCompleted['dateCompleted'] = 'OVERRIDE'
    expCompleted['resultReturnCode'] = 0
    a = JobExecutionClass(jobObj)
    resDict = dict(a.__dict__)
    tim = from_iso8601(a.dateCreated)
    resDict['dateCreated'] = 'OVERRIDE'
    resDict['guid'] = 'OVERRIDE'
    self.assertJSONStringsEqual(resDict, expPending)
    a.execute(appObj.jobExecutor)
    self.assertEqual(a.stage, 'Completed')
    resDict = dict(a.__dict__)
    resDict['dateCreated'] = 'OVERRIDE'
    resDict['dateStarted'] = 'OVERRIDE'
    resDict['dateCompleted'] = 'OVERRIDE'
    resDict['guid'] = 'OVERRIDE'
    tim = from_iso8601(a.dateStarted)
    self.assertTimeCloseToCurrent(tim)
    tim = from_iso8601(a.dateCompleted)
    self.assertTimeCloseToCurrent(tim)
    self.assertJSONStringsEqual(resDict, expCompleted)
