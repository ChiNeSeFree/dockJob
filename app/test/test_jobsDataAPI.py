from TestHelperSuperClass import testHelperAPIClient

import json
from baseapp_for_restapi_backend_with_swagger import from_iso8601
from appObj import appObj
import datetime
import pytz
import time
from dateutil.relativedelta import relativedelta
from commonJSONStrings import data_simpleJobCreateParams, data_simpleManualJobCreateParams, data_simpleJobCreateExpRes, data_simpleJobExecutionCreateExpRes

class test_jobsData(testHelperAPIClient):
  def assertJSONJobStringsEqual(self, result,expectedResult):
    #ignores fields that may be different
    result['guid'] = expectedResult['guid']
    result['nextScheduledRun'] = expectedResult['nextScheduledRun']
    result['creationDate'] = expectedResult['creationDate']
    result['lastUpdateDate'] = expectedResult['lastUpdateDate']
    self.assertJSONStringsEqual(result, expectedResult);

  def test_JobCreate(self):
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    self.assertEqual(result.status_code, 200)
    resultJSON = json.loads(result.get_data(as_text=True))
    self.assertEqual(len(resultJSON['guid']), 36, msg='Invalid GUID - must be 36 chars')
    self.assertEqual(resultJSON['creationDate'], resultJSON['lastUpdateDate'], msg='Creation date dosen''t match last update')
    tim = from_iso8601(resultJSON['creationDate'])
    self.assertTimeCloseToCurrent(tim)
    self.assertJSONJobStringsEqual(resultJSON, data_simpleJobCreateExpRes)
    self.assertCorrectTotalJobs(1)

  def test_JobCreateDuplicateErrors(self):
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    self.assertEqual(result.status_code, 200, msg='First job creation should have worked')
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    self.assertEqual(result.status_code, 400, msg='Duplicate job creation didn''t return 400')

  def test_JobCreateBadValidation(self):
    params = {
      "name": "TestJob",
      "repetitionInterval": "INVALIDREPINT:03",
      "command": "ls",
      "enabled": True
    }
    result = self.testClient.post('/api/jobs/', data=json.dumps(params), content_type='application/json')
    self.assertEqual(result.status_code, 400, msg='Badly formatted job didn''t  return 400')

  def test_JobCreateBlankRepititionInterval(self):
    params = {
      "name": "TestJob",
      "repetitionInterval": None,
      "command": "ls",
      "enabled": True
    }
    result = self.testClient.post('/api/jobs/', data=json.dumps(params), content_type='application/json')
    self.assertEqual(result.status_code, 400, msg='Blank repitition was accepted (Use empty string)')

  def test_JobCreateEmptyRepititionInterval(self):
    params = {
      "name": "TestJob",
      "repetitionInterval": '',
      "command": "ls",
      "enabled": False
    }
    result = self.testClient.post('/api/jobs/', data=json.dumps(params), content_type='application/json')
    self.assertEqual(result.status_code, 200, msg='Empty repitition interval not accepted')

  def test_jobCreateAndQueryBackByGUID(self):
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    resultJSON = json.loads(result.get_data(as_text=True))
    self.assertEqual(result.status_code, 200, msg='First job creation should have worked')
    result2 = self.testClient.get('/api/jobs/' + resultJSON['guid'])
    self.assertEqual(result2.status_code, 200, msg='Read back record')
    result2JSON = json.loads(result2.get_data(as_text=True))
    self.assertJSONJobStringsEqual(resultJSON, data_simpleJobCreateExpRes);

  def test_jobGetInvalid(self):
    result = self.testClient.get('/api/jobs/INVALID_KEY')
    self.assertEqual(result.status_code, 400, msg='Didn''t return not found job')

  def test_jobCreateAndQueryBackByName(self):
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    resultJSON = json.loads(result.get_data(as_text=True))
    self.assertEqual(result.status_code, 200, msg='First job creation should have worked')
    result2 = self.testClient.get('/api/jobs/' + resultJSON['name'])
    self.assertEqual(result2.status_code, 200, msg='Read back record')
    result2JSON = json.loads(result2.get_data(as_text=True))
    self.assertJSONJobStringsEqual(resultJSON, data_simpleJobCreateExpRes);

  def test_jobCreateAndQueryBackByName(self):
    numTestRecords = 6
    param = self.createJobs(numTestRecords, data_simpleJobCreateParams)
    result2 = self.testClient.get('/api/jobs/')
    self.assertEqual(result2.status_code, 200, msg='Fetch failed')
    result2JSON = json.loads(result2.get_data(as_text=True))
    expPaginationResult = {'offset': 0, 'pagesize': 100, 'total': numTestRecords}
    self.assertJSONStringsEqual(result2JSON["pagination"], expPaginationResult);
    self.assertEqual(len(result2JSON["result"]),numTestRecords,msg="Wrong number of returned results")
    exp = dict(data_simpleJobCreateExpRes)
    for cur in range(0,numTestRecords):
      thisParam = self.findRecord(param, result2JSON["result"][cur]['name'])
      exp['name'] = thisParam['name']
      self.assertJSONJobStringsEqual(result2JSON["result"][cur], exp)

  def test_jobQueryPaginationTests(self):
    exp = dict(data_simpleJobCreateExpRes)
    numTestRecords = 45
    pagesize = 15
    param = self.createJobs(numTestRecords, data_simpleJobCreateParams)

    #Query back first page of 15
    result2 = self.testClient.get('/api/jobs/?pagesize=' + str(pagesize))
    self.assertEqual(result2.status_code, 200, msg='Fetch failed')
    result2JSON = json.loads(result2.get_data(as_text=True))
    expPaginationResult = {'offset': 0, 'pagesize': pagesize, 'total': numTestRecords}
    self.assertJSONStringsEqual(result2JSON["pagination"], expPaginationResult);
    self.assertEqual(len(result2JSON["result"]),pagesize,msg="Wrong number of returned results in first page")
    for cur in range(0,pagesize):
      exp['name'] = param[cur]['name']
      self.assertJSONJobStringsEqual(result2JSON["result"][cur], exp);

    #Query back 2nd page of 15
    offset = 15
    result2 = self.testClient.get('/api/jobs/?pagesize=' + str(pagesize) + '&offset=' + str(offset))
    self.assertEqual(result2.status_code, 200, msg='Fetch failed')
    result2JSON = json.loads(result2.get_data(as_text=True))
    expPaginationResult = {'offset': offset, 'pagesize': pagesize, 'total': numTestRecords}
    self.assertJSONStringsEqual(result2JSON["pagination"], expPaginationResult);
    self.assertEqual(len(result2JSON["result"]),pagesize,msg="Wrong number of returned results in second page")
    for cur in range(0,pagesize):
      exp['name'] = param[cur + offset]['name']
      self.assertJSONJobStringsEqual(result2JSON["result"][cur], exp);

    #Query back 3rd final page (only 5 left)
    offset = 30
    result2 = self.testClient.get('/api/jobs/?pagesize=' + str(pagesize) + '&offset=' + str(offset))
    self.assertEqual(result2.status_code, 200, msg='Fetch failed')
    result2JSON = json.loads(result2.get_data(as_text=True))
    expPaginationResult = {'offset': offset, 'pagesize': pagesize, 'total': numTestRecords}
    self.assertJSONStringsEqual(result2JSON["pagination"], expPaginationResult);
    self.assertEqual(len(result2JSON["result"]),pagesize,msg="Wrong number of returned results in last page")
    for cur in range(0,numTestRecords - offset):
      exp['name'] = param[cur + offset]['name']
      self.assertJSONJobStringsEqual(result2JSON["result"][cur], exp);

  def test_jobDeleteByGUID(self):
    backgroundData = dict(data_simpleJobCreateParams)
    backgroundData['name'] = 'BackgroundData'
    self.createJobs(10, data_simpleJobCreateParams)
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    resultJSON = json.loads(result.get_data(as_text=True))
    self.assertEqual(result.status_code, 200, msg='First job creation should have worked')
    result2 = self.testClient.delete('/api/jobs/' + resultJSON['guid'])
    self.assertEqual(result2.status_code, 200, msg='Didn''t delete record')
    result2JSON = json.loads(result2.get_data(as_text=True))
    self.assertJSONJobStringsEqual(result2JSON, data_simpleJobCreateExpRes);
    result3 = self.testClient.get('/api/jobs/' + resultJSON['name'])
    self.assertEqual(result3.status_code, 400, msg='Managed to retrieve deleted job by name')
    result4 = self.testClient.get('/api/jobs/' + resultJSON['guid'])
    self.assertEqual(result4.status_code, 400, msg='Managed to retrieve deleted job by guid')
    self.assertCorrectTotalJobs(10)

  def test_jobDeleteByName(self):
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    resultJSON = json.loads(result.get_data(as_text=True))
    self.assertEqual(result.status_code, 200, msg='First job creation should have worked')
    guid_of_job_to_be_deleted = resultJSON['guid']
    name_of_job_to_be_deleted = resultJSON['name']
    # create a second job which won't be deleted
    p2 = dict(data_simpleJobCreateParams)
    p2['name'] = 'JobNotToBeDeleted'
    result = self.testClient.post('/api/jobs/', data=json.dumps(p2), content_type='application/json')
    resultJSON = json.loads(result.get_data(as_text=True))
    self.assertEqual(result.status_code, 200, msg='Second job creation should have worked')

    #Delete record by name
    delete_result = self.testClient.delete('/api/jobs/' + name_of_job_to_be_deleted)
    self.assertEqual(delete_result.status_code, 200, msg='Didn''t delete record')
    delete_resultJSON = json.loads(delete_result.get_data(as_text=True))
    self.assertJSONJobStringsEqual(delete_resultJSON, data_simpleJobCreateExpRes);

    #Further checks
    result3 = self.testClient.get('/api/jobs/' + name_of_job_to_be_deleted)
    self.assertEqual(result3.status_code, 400, msg='Managed to retrieve deleted job by name')
    result4 = self.testClient.get('/api/jobs/' + guid_of_job_to_be_deleted)
    self.assertEqual(result4.status_code, 400, msg='Managed to retrieve deleted job by guid')
    self.assertCorrectTotalJobs(1)

  def test_jobDeleteByGUIDNotExist(self):
    result2 = self.testClient.delete('/api/jobs/' + 'BAD-GUID-OR-NAME')
    self.assertEqual(result2.status_code, 400, msg='Deleted a record')
    self.assertCorrectTotalJobs(0)

  def test_jobFilter(self):
    numShown = 3
    exp = dict(data_simpleJobCreateExpRes)
    p1 = dict(data_simpleJobCreateParams)
    p1['name'] = 'NotIntrested'
    p2 = dict(data_simpleJobCreateParams)
    p2['name'] = 'ShowInFilterPrr'
    p3 = dict(data_simpleJobCreateParams)
    p3['name'] = 'HideAway'
    param1 = self.createJobs(6, p1)
    param2 = self.createJobs(numShown, p2)
    param3 = self.createJobs(8, p3)
    
    #Now query back only our showed records
    # using simple non-paginated query
    result2 = self.testClient.get('/api/jobs/?query=Prr')
    self.assertEqual(result2.status_code, 200, msg='Fetch failed')
    result2JSON = json.loads(result2.get_data(as_text=True))
    expPaginationResult = {'offset': 0, 'pagesize': 100, 'total': numShown}
    self.assertJSONStringsEqual(result2JSON["pagination"], expPaginationResult);
    for cur in range(0,numShown):
      exp['name'] = param2[cur]['name']
      self.assertJSONJobStringsEqual(result2JSON["result"][cur], exp);

  def test_jobFilterCommand(self):
    numShown = 3
    exp = dict(data_simpleJobCreateExpRes)
    p1 = dict(data_simpleJobCreateParams)
    p1['name'] = 'NotIntrested'
    p2 = dict(data_simpleJobCreateParams)
    p2['name'] = 'ShowInFilterPrr'
    p2['command'] = 'xxxfeEdComm'
    p3 = dict(data_simpleJobCreateParams)
    p3['name'] = 'HideAway'
    param1 = self.createJobs(6, p1)
    param2 = self.createJobs(numShown, p2)
    param3 = self.createJobs(8, p3)
    
    #Now query back only our showed records
    # using simple non-paginated query
    result2 = self.testClient.get('/api/jobs/?query=FEed')
    self.assertEqual(result2.status_code, 200, msg='Fetch failed')
    result2JSON = json.loads(result2.get_data(as_text=True))
    expPaginationResult = {'offset': 0, 'pagesize': 100, 'total': numShown}
    self.assertJSONStringsEqual(result2JSON["pagination"], expPaginationResult);
    for cur in range(0,numShown):
      exp['name'] = param2[cur]['name']
      exp['command'] = param2[cur]['command']
      self.assertJSONJobStringsEqual(result2JSON["result"][cur], exp);

  def test_jobFilterTwoClausesPositive(self):
    numShown = 3
    exp = dict(data_simpleJobCreateExpRes)
    p1 = dict(data_simpleJobCreateParams)
    p1['name'] = 'NotIntrested'
    p2 = dict(data_simpleJobCreateParams)
    p2['name'] = 'ShowInFilterPrr'
    p3 = dict(data_simpleJobCreateParams)
    p3['name'] = 'HideAway'
    param1 = self.createJobs(6, p1)
    param2 = self.createJobs(numShown, p2)
    param3 = self.createJobs(8, p3)
    
    #Now query back only our showed records
    # using simple non-paginated query
    result2 = self.testClient.get('/api/jobs/?query=in%20filt')
    self.assertEqual(result2.status_code, 200, msg='Fetch failed')
    result2JSON = json.loads(result2.get_data(as_text=True))
    expPaginationResult = {'offset': 0, 'pagesize': 100, 'total': numShown}
    self.assertJSONStringsEqual(result2JSON["pagination"], expPaginationResult);
    for cur in range(0,numShown):
      exp['name'] = param2[cur]['name']
      self.assertJSONJobStringsEqual(result2JSON["result"][cur], exp);

  def test_jobFilterTwoClausesNegative(self):
    numNotShown = 3
    exp = dict(data_simpleJobCreateExpRes)
    p1 = dict(data_simpleJobCreateParams)
    p1['name'] = 'NotIntrested'
    p2 = dict(data_simpleJobCreateParams)
    p2['name'] = 'ShowInFilterPrr'
    p3 = dict(data_simpleJobCreateParams)
    p3['name'] = 'HideAway'
    param1 = self.createJobs(6, p1)
    param2 = self.createJobs(numNotShown, p2)
    param3 = self.createJobs(8, p3)
    
    #Now query back only our showed records
    # using simple non-paginated query
    result2 = self.testClient.get('/api/jobs/?query=in%20fiiilt')
    self.assertEqual(result2.status_code, 200, msg='Fetch failed')
    result2JSON = json.loads(result2.get_data(as_text=True))
    expPaginationResult = {'offset': 0, 'pagesize': 100, 'total': 0}
    self.assertJSONStringsEqual(result2JSON["pagination"], expPaginationResult);

  def test_submitJobForExecution(self):
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    self.assertEqual(result.status_code, 200)
    resultJSON = json.loads(result.get_data(as_text=True))
    jobGUID = resultJSON['guid']
    jobCommand = resultJSON['command']
    self.assertEqual(len(jobGUID),36, msg='Invalid job GUID - must be 36 chars')

    resultJSON2 = self.addExecution(jobGUID, 'TestExecutionName')
    exp = dict(data_simpleJobExecutionCreateExpRes)
    resultJSON2['guid'] = exp['guid']
    resultJSON2['dateCreated'] = exp['dateCreated']
    resultJSON2['dateStarted'] = exp['dateStarted']
    resultJSON2['dateCompleted'] = exp['dateCompleted']

    exp['jobCommand'] = jobCommand
    exp['jobGUID'] = jobGUID

    self.assertJSONStringsEqual(resultJSON2, exp);
    
  def test_getJobExecutions(self):
    execution_guids = self.setupJobsAndExecutions(data_simpleJobCreateParams)

  def test_deleteJobRemovedExecutionLogs(self):
    execution_guids = self.setupJobsAndExecutions(data_simpleJobCreateParams)
    testExecutionGUID = execution_guids['002_002']

    #Retrieve Execution Data to find jobGUID
    result = self.testClient.get('/api/executions/' + testExecutionGUID)
    self.assertEqual(result.status_code, 200, msg='Read back failed')
    resultJSON = json.loads(result.get_data(as_text=True))
    self.assertEqual(resultJSON['guid'],testExecutionGUID,msg='Query Exection error - wrong execution returned')
    testJobGUID = resultJSON['jobGUID']

    #Delete Job
    result2 = self.testClient.delete('/api/jobs/' + testJobGUID)
    self.assertEqual(result2.status_code, 200, msg='Didn''t delete record')
    time.sleep(0.1) #This test fails sometimes. I think it is because sometimes the delete thread gets overtaken
                    # by the following get so I added this sleep
                    #  sleep didn't work :(

    #requery execution to check if it has been deleted
    result = self.testClient.get('/api/executions/' + testExecutionGUID)
    resultJSON = json.loads(result.get_data(as_text=True))
    print(resultJSON)
    self.assertEqual(result.status_code, 400, msg='Exectuion for deleted job still in system')

  def createJobWithRepInterval(self, interval):
    jobCreate = dict(data_simpleJobCreateParams)
    jobCreate['repetitionInterval'] = interval
    jobCreate['name'] = 'Job_with_ri_' + interval
    result = self.testClient.post('/api/jobs/', data=json.dumps(jobCreate), content_type='application/json')
    resultJSON = json.loads(result.get_data(as_text=True))
    if result.status_code != 200:
      print(resultJSON)
    self.assertEqual(result.status_code, 200, msg='Job creation for interval ' + interval + ' failed')
    return resultJSON['guid']

  def createInactiveJob(self, name):
    jobCreate = dict(data_simpleJobCreateParams)
    jobCreate['repetitionInterval'] = ''
    jobCreate['enabled'] = False
    jobCreate['name'] = name
    result = self.testClient.post('/api/jobs/', data=json.dumps(jobCreate), content_type='application/json')
    resultJSON = json.loads(result.get_data(as_text=True))
    if result.status_code != 200:
      print(resultJSON)
    self.assertEqual(result.status_code, 200, msg='Job creation for inactive job named ' + name + ' failed')
    return resultJSON['guid']

  def test_getNextJobToExecuteOneJobInSystem(self):
    jobGUID = self.createJobWithRepInterval('HOURLY:55')
    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertNotEqual(nextExecute, None, msg='Next job to execute should not be none as we have one hourly job')
    self.assertEqual(nextExecute.guid,jobGUID)

  def test_getNextJobToExecuteGetsRightJob(self):
    jobGUID55 = self.createJobWithRepInterval('HOURLY:55')
    jobGUID05 = self.createJobWithRepInterval('HOURLY:05')
    jobGUID35 = self.createJobWithRepInterval('HOURLY:35')
    jobGUID25 = self.createJobWithRepInterval('HOURLY:25')
    jobGUID45 = self.createJobWithRepInterval('HOURLY:45')
    appObj.appData['jobsData'].recaculateExecutionTimesBasedonNewTime(datetime.datetime(2016,1,5,14,2,59,0,pytz.timezone('UTC')))
    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertNotEqual(nextExecute, None, msg='Next job to execute should not be none as we have one hourly job')
    self.assertEqual(nextExecute.guid,jobGUID05, msg='Wrong next job selected. The next job is the one that runs at ' + nextExecute.nextScheduledRun)

    appObj.appData['jobsData'].recaculateExecutionTimesBasedonNewTime(datetime.datetime(2016,1,5,15,6,59,0,pytz.timezone('UTC')))
    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertNotEqual(nextExecute, None, msg='Next job to execute should not be none as we have one hourly job')
    self.assertEqual(nextExecute.guid,jobGUID25, msg='Wrong next job selected. The next job is the one that runs at ' + nextExecute.nextScheduledRun)

    appObj.appData['jobsData'].recaculateExecutionTimesBasedonNewTime(datetime.datetime(2016,1,5,15,46,59,0,pytz.timezone('UTC')))
    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertNotEqual(nextExecute, None, msg='Next job to execute should not be none as we have one hourly job')
    self.assertEqual(nextExecute.guid,jobGUID55, msg='Wrong next job selected. The next job is the one that runs at ' + nextExecute.nextScheduledRun)

  def test_deleteNextJobToExecute(self):
    jobGUID55 = self.createJobWithRepInterval('HOURLY:55')
    jobGUID05 = self.createJobWithRepInterval('HOURLY:05')
    jobGUID35 = self.createJobWithRepInterval('HOURLY:35')
    jobGUID25 = self.createJobWithRepInterval('HOURLY:25')
    jobGUID45 = self.createJobWithRepInterval('HOURLY:45')
    appObj.appData['jobsData'].recaculateExecutionTimesBasedonNewTime(datetime.datetime(2016,1,5,14,2,59,0,pytz.timezone('UTC')))
    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertEqual(nextExecute.guid,jobGUID05, msg='Wrong next job selected. The next job is the one that runs at ' + nextExecute.nextScheduledRun)

    # Delete the job that runs at 5 past the hour (It is the next to execute)
    result2 = self.testClient.delete('/api/jobs/' + jobGUID05)
    self.assertEqual(result2.status_code, 200, msg='Didn''t delete job')

    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertEqual(nextExecute.guid,jobGUID25, msg='After deleting the job that is next to execute the 25 minutes past job should be next to execute')

  def test_nextExecuteWithOnlyInactive(self):
    self.createInactiveJob('Inactive 001')
    self.createInactiveJob('Inactive 002')
    self.createInactiveJob('Inactive 003')
    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertEqual(nextExecute,None)

## Inactive Jobs ignored
  def test_inactiveJobsDoNotAffectNextExecute(self):
    jobGUID55 = self.createJobWithRepInterval('HOURLY:55')
    self.createInactiveJob('Inactive 001')
    jobGUID05 = self.createJobWithRepInterval('HOURLY:05')
    self.createInactiveJob('Inactive 002')
    jobGUID35 = self.createJobWithRepInterval('HOURLY:35')
    jobGUID25 = self.createJobWithRepInterval('HOURLY:25')
    self.createInactiveJob('Inactive 003')
    jobGUID45 = self.createJobWithRepInterval('HOURLY:45')
    appObj.appData['jobsData'].recaculateExecutionTimesBasedonNewTime(datetime.datetime(2016,1,5,14,2,59,0,pytz.timezone('UTC')))
    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertEqual(nextExecute.guid,jobGUID05, msg='Wrong next job selected. The next job is the one that runs at ' + nextExecute.nextScheduledRun)

  def test_jobExecutionInFutureNotExecuted(self):
    ## Execute job updates the next execute
    jobGUID05 = self.createJobWithRepInterval('HOURLY:05')
    jobGUID25 = self.createJobWithRepInterval('HOURLY:25')
    appObj.appData['jobsData'].recaculateExecutionTimesBasedonNewTime(datetime.datetime(2016,1,5,14,2,59,0,pytz.timezone('UTC')))
    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertEqual(nextExecute.guid,jobGUID05, msg='Wrong next job selected. The next job is the one that runs at ' + nextExecute.nextScheduledRun)

    # Run execute loop a few times
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,1,59,0,pytz.timezone('UTC')))
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,2,59,0,pytz.timezone('UTC')))
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,3,59,0,pytz.timezone('UTC')))

    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertEqual(nextExecute.guid,jobGUID05, msg='Wrong next job selected. Should not have changed from 05')

  def test_executeJobDoseNotExecuteWhenItsNotTime(self):
    jobGUID05 = self.createJobWithRepInterval('HOURLY:05')
    appObj.appData['jobsData'].recaculateExecutionTimesBasedonNewTime(datetime.datetime(2016,1,5,14,2,59,0,pytz.timezone('UTC')))
    # Run execute loop a few times
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,1,59,0,pytz.timezone('UTC')))
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,2,59,0,pytz.timezone('UTC')))
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,3,59,0,pytz.timezone('UTC')))

    #Query back executions
    queryJobExecutionsResult = self.testClient.get('/api/jobs/' + jobGUID05 + '/execution')
    self.assertEqual(queryJobExecutionsResult.status_code, 200)
    queryJobExecutionsResultJSON = json.loads(queryJobExecutionsResult.get_data(as_text=True))
    self.assertEqual(queryJobExecutionsResultJSON['pagination']['total'], 0, msg='Found executions')

  def test_executeJobUpdatesNextExecute(self):
    ## Execute job updates the next execute
    jobGUID05 = self.createJobWithRepInterval('HOURLY:05')
    jobGUID25 = self.createJobWithRepInterval('HOURLY:25')
    appObj.appData['jobsData'].recaculateExecutionTimesBasedonNewTime(datetime.datetime(2016,1,5,14,2,59,0,pytz.timezone('UTC')))
    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertEqual(nextExecute.guid,jobGUID05, msg='Wrong next job selected. The next job is the one that runs at ' + nextExecute.nextScheduledRun)

    # Run execute loop a few times
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,3,59,0,pytz.timezone('UTC')))
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,6,59,0,pytz.timezone('UTC')))
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,9,59,0,pytz.timezone('UTC')))
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,14,59,0,pytz.timezone('UTC')))
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,19,59,0,pytz.timezone('UTC')))
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,23,59,0,pytz.timezone('UTC')))

    nextExecute = appObj.appData['jobsData'].getNextJobToExecute()
    self.assertEqual(nextExecute.guid,jobGUID25, msg='Wrong next job selected. Should have executed the 05 one and now the next to execute should be 25')

    # Check the execution log to make sure job jobGUID05 was executed
    queryJobExecutionsResult = self.testClient.get('/api/jobs/' + jobGUID05 + '/execution')
    self.assertEqual(queryJobExecutionsResult.status_code, 200)
    queryJobExecutionsResultJSON = json.loads(queryJobExecutionsResult.get_data(as_text=True))
    self.assertEqual(queryJobExecutionsResultJSON['pagination']['total'], 1, msg='Ditn''t find execution for 05 job')

    # Check the execution log to make sure job jobGUID25 was not executed
    queryJobExecutionsResult2 = self.testClient.get('/api/jobs/' + jobGUID25 + '/execution')
    self.assertEqual(queryJobExecutionsResult2.status_code, 200)
    queryJobExecutionsResult2JSON = json.loads(queryJobExecutionsResult2.get_data(as_text=True))
    self.assertEqual(queryJobExecutionsResult2JSON['pagination']['total'], 0, msg='Found executions for 25 job but it should not have been run')

  def test_oldRunLogsArePurgedAfter1Week(self):
    #This will add a job, manually run it check it has a execution log then run loop iteration after purge interval later and then recheck execution log to make sure it has gone
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleManualJobCreateParams), content_type='application/json')
    self.assertEqual(result.status_code, 200, msg='Wrong status ' + str(result))
    resultJSON = json.loads(result.get_data(as_text=True))
    jobGUID = resultJSON['guid']

    resultJSON2 = self.addExecution(jobGUID, 'TestExecutionName')

    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,3,59,0,pytz.timezone('UTC')))

    # Check we have an execution log
    queryJobExecutionsResult = self.testClient.get('/api/jobs/' + jobGUID + '/execution')
    self.assertEqual(queryJobExecutionsResult.status_code, 200)
    queryJobExecutionsResultJSON = json.loads(queryJobExecutionsResult.get_data(as_text=True))
    self.assertEqual(queryJobExecutionsResultJSON['pagination']['total'], 1, msg='Didn''t find execution for job')
    self.assertEqual(queryJobExecutionsResultJSON["result"][0]['stage'], 'Completed', msg='Job not completed')
    self.assertNotEqual(queryJobExecutionsResultJSON["result"][0]['dateCompleted'], None, msg='Job execution didn''t complete')
    dateCompleted = from_iso8601(queryJobExecutionsResultJSON["result"][0]['dateCompleted'])
    self.assertEqual(str(dateCompleted.tzinfo),'tzutc()',msg='date completed not returned in UTC')

    # Test we still have execution in one days time (from date completed)
    timeToTest = dateCompleted + datetime.timedelta(days=1)
    appObj.jobExecutor.loopIteration(timeToTest)
    queryJobExecutionsResult = self.testClient.get('/api/jobs/' + jobGUID + '/execution')
    self.assertEqual(queryJobExecutionsResult.status_code, 200)
    queryJobExecutionsResultJSON = json.loads(queryJobExecutionsResult.get_data(as_text=True))
    self.assertEqual(queryJobExecutionsResultJSON['pagination']['total'], 1, msg='Didn''t find execution for job')
    self.assertEqual(queryJobExecutionsResultJSON["result"][0]['stage'], 'Completed', msg='Job not completed')
    self.assertNotEqual(queryJobExecutionsResultJSON["result"][0]['dateCompleted'], None, msg='Job execution didn''t complete')

    # Test we do not have execution in eight days time
    timeToTest = dateCompleted + datetime.timedelta(days=8)
    appObj.jobExecutor.loopIteration(timeToTest)
    queryJobExecutionsResult = self.testClient.get('/api/jobs/' + jobGUID + '/execution')
    self.assertEqual(queryJobExecutionsResult.status_code, 200)
    queryJobExecutionsResultJSON = json.loads(queryJobExecutionsResult.get_data(as_text=True))
    self.assertEqual(queryJobExecutionsResultJSON['pagination']['total'], 0, msg='Found execution but it should have been purged')

  def test_jobExecutionFillsInDateStartedAndCompleted(self):
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleManualJobCreateParams), content_type='application/json')
    self.assertEqual(result.status_code, 200)
    resultJSON = json.loads(result.get_data(as_text=True))
    jobGUID = resultJSON['guid']

    resultJSON2 = self.addExecution(jobGUID, 'TestExecutionName')

    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,3,55,0,pytz.timezone('UTC')))

    # Check we have an execution log
    queryJobExecutionsResult = self.testClient.get('/api/jobs/' + jobGUID + '/execution')
    self.assertEqual(queryJobExecutionsResult.status_code, 200)
    queryJobExecutionsResultJSON = json.loads(queryJobExecutionsResult.get_data(as_text=True))
    self.assertEqual(queryJobExecutionsResultJSON['pagination']['total'], 1, msg='Didn''t find execution for job')
    print(queryJobExecutionsResultJSON)
    self.assertEqual(queryJobExecutionsResultJSON["result"][0]['stage'], 'Completed', msg='Job not completed')
    self.assertNotEqual(queryJobExecutionsResultJSON["result"][0]['dateStarted'], None, msg='Date started not filled in')
    self.assertNotEqual(queryJobExecutionsResultJSON["result"][0]['dateCompleted'], None, msg='Date completed not filled in')

  def test_jobExecutionFillsInJobLastRunDateAndReturnCode(self):
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleManualJobCreateParams), content_type='application/json')
    self.assertEqual(result.status_code, 200)
    resultJSON = json.loads(result.get_data(as_text=True))
    jobGUID = resultJSON['guid']

    resultJSON2 = self.addExecution(jobGUID, 'TestExecutionName')
    executionGUID = resultJSON2['guid']

    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,3,55,0,pytz.timezone('UTC')))

    # Check Job info
    queryJobResult = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(queryJobResult.status_code, 200)
    queryJobResultJSON = json.loads(queryJobResult.get_data(as_text=True))
    self.assertNotEqual(queryJobResultJSON['lastRunDate'],None, msg='last Run Date not set against job')
    tim = from_iso8601(queryJobResultJSON['lastRunDate'])
    self.assertTimeCloseToCurrent(tim, msg='last Run date not recently set')

    self.assertEqual(queryJobResultJSON['lastRunReturnCode'],0, msg='last Run return code not sucess')
    self.assertEqual(queryJobResultJSON['lastRunExecutionGUID'],executionGUID, msg='last run Execution GUID not correct')

  def test_updateJobName(self):
    newJobNameValue = 'newJobNameValueXXX'
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    resultJSON = dict(json.loads(result.get_data(as_text=True)))
    self.assertEqual(result.status_code, 200, msg='First job creation should have worked')
    jobGUID = resultJSON['guid']
    origName = resultJSON['name']

    #Read back job to make sure it has correct value
    result2 = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(result2.status_code, 200, msg='Read back record')
    result2JSON = dict(json.loads(result2.get_data(as_text=True)))
    self.assertJSONJobStringsEqual(resultJSON, data_simpleJobCreateExpRes);

    alteredResults = dict(data_simpleJobCreateExpRes)
    alteredResults['name'] = newJobNameValue
    alteredResults['guid'] = jobGUID
    alteredResults['lastUpdateDate'] = result2JSON['lastUpdateDate']
    alteredResults['creationDate'] = result2JSON['creationDate']
    alteredResults['lastRunDate'] = result2JSON['lastRunDate']
    alteredResults['nextScheduledRun'] = result2JSON['nextScheduledRun']

    #Update JobName to new value
    updateNameInput = dict(data_simpleJobCreateParams)
    updateNameInput['name'] = newJobNameValue
    updateJobNameResult = self.testClient.put('/api/jobs/' + jobGUID, data=json.dumps(updateNameInput), content_type='application/json')
    self.assertEqual(updateJobNameResult.status_code, 200, msg='Put call did not give correct status')
    updateJobNameResultJSON = dict(json.loads(updateJobNameResult.get_data(as_text=True)))
    self.assertJSONJobStringsEqual(updateJobNameResultJSON, alteredResults);

    #Read back job by GUID to make sure it has correct value with new jobNAme
    result3 = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(result3.status_code, 200, msg='Read back record by guid after name change failed')
    result3JSON = dict(json.loads(result3.get_data(as_text=True)))
    self.assertJSONJobStringsEqual(result3JSON, alteredResults);

    #Read back job by NAME works
    result6 = self.testClient.get('/api/jobs/' + newJobNameValue)
    self.assertEqual(result6.status_code, 200, msg='Read back record by job name after name change failed')
    result6JSON = dict(json.loads(result6.get_data(as_text=True)))
    self.assertJSONJobStringsEqual(result6JSON, alteredResults);

    #Read back job by Old Name Fails
    result3 = self.testClient.get('/api/jobs/' + origName)
    self.assertEqual(result3.status_code, 400, msg='Read back record by oldname change should have failed')


  def test_updateJobNameToInvalidValue(self):
    newJobNameValue = 'x'
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    resultJSON = dict(json.loads(result.get_data(as_text=True)))
    self.assertEqual(result.status_code, 200, msg='First job creation should have worked')
    jobGUID = resultJSON['guid']
    origName = resultJSON['name']

    #Read back job to make sure it has correct value
    result2 = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(result2.status_code, 200, msg='Read back record')
    result2JSON = dict(json.loads(result2.get_data(as_text=True)))
    self.assertJSONJobStringsEqual(resultJSON, data_simpleJobCreateExpRes);

    alteredResults = dict(data_simpleJobCreateExpRes)
    alteredResults['name'] = newJobNameValue
    alteredResults['guid'] = jobGUID
    alteredResults['lastUpdateDate'] = result2JSON['lastUpdateDate']
    alteredResults['creationDate'] = result2JSON['creationDate']
    alteredResults['lastRunDate'] = result2JSON['lastRunDate']
    alteredResults['nextScheduledRun'] = result2JSON['nextScheduledRun']

    #Update JobName to new value
    updateNameInput = dict(data_simpleJobCreateParams)
    updateNameInput['name'] = newJobNameValue
    updateJobNameResult = self.testClient.put('/api/jobs/' + jobGUID, data=json.dumps(updateNameInput), content_type='application/json')
    self.assertEqual(updateJobNameResult.status_code, 400, msg='Put call did not give correct status')
    updateJobNameResultJSON = dict(json.loads(updateJobNameResult.get_data(as_text=True)))

    #Read back job by GUID to make sure it has correct value with new jobNAme
    result3 = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(result3.status_code, 200, msg='Read back record by guid after name change failed')
    result3JSON = dict(json.loads(result3.get_data(as_text=True)))
    self.assertJSONJobStringsEqual(result3JSON, data_simpleJobCreateExpRes);

    #Read back job by NAME works
    result6 = self.testClient.get('/api/jobs/' + origName)
    self.assertEqual(result6.status_code, 200, msg='Read back record by job name after name change failed')
    result6JSON = dict(json.loads(result6.get_data(as_text=True)))
    self.assertJSONJobStringsEqual(result6JSON, data_simpleJobCreateExpRes);

  def test_updateRepititionIntervalToInvalidValue(self):
    newJobNameValue = 'TestJobWithInvalidRI'
    newRI = 'Invalid RI Value'
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    resultJSON = dict(json.loads(result.get_data(as_text=True)))
    self.assertEqual(result.status_code, 200, msg='First job creation should have worked')
    jobGUID = resultJSON['guid']
    origName = resultJSON['name']

    #Read back job to make sure it has correct value
    result2 = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(result2.status_code, 200, msg='Read back record')
    result2JSON = dict(json.loads(result2.get_data(as_text=True)))
    self.assertJSONJobStringsEqual(resultJSON, data_simpleJobCreateExpRes);

    alteredResults = dict(data_simpleJobCreateExpRes)
    alteredResults['name'] = newJobNameValue
    alteredResults['guid'] = jobGUID
    alteredResults['lastUpdateDate'] = result2JSON['lastUpdateDate']
    alteredResults['creationDate'] = result2JSON['creationDate']
    alteredResults['lastRunDate'] = result2JSON['lastRunDate']
    alteredResults['nextScheduledRun'] = result2JSON['nextScheduledRun']

    #Update JobName to new value
    updateNameInput = dict(data_simpleJobCreateParams)
    updateNameInput['name'] = newJobNameValue
    updateNameInput['repetitionInterval'] = newRI
    updateJobNameResult = self.testClient.put('/api/jobs/' + jobGUID, data=json.dumps(updateNameInput), content_type='application/json')
    self.assertEqual(updateJobNameResult.status_code, 400, msg='Put call did not give correct status')
    updateJobNameResultJSON = dict(json.loads(updateJobNameResult.get_data(as_text=True)))

    #Read back job by GUID to make sure it has correct value with new jobName
    result3 = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(result3.status_code, 200, msg='Read back record by guid after name change failed')
    result3JSON = dict(json.loads(result3.get_data(as_text=True)))
    self.assertJSONJobStringsEqual(result3JSON, data_simpleJobCreateExpRes);

    #Read back job by NAME works
    result6 = self.testClient.get('/api/jobs/' + origName)
    self.assertEqual(result6.status_code, 200, msg='Read back record by job name after name change failed')
    result6JSON = dict(json.loads(result6.get_data(as_text=True)))
    self.assertJSONJobStringsEqual(result6JSON, data_simpleJobCreateExpRes);

  def test_getJobHasProperlyFormattedRepititionInterval_singledigit(self):
    single_digit_hourly = dict(data_simpleJobCreateParams)
    single_digit_hourly['repetitionInterval'] = 'HOURLY:3'
    result = self.testClient.post('/api/jobs/', data=json.dumps(single_digit_hourly), content_type='application/json')
    self.assertEqual(result.status_code, 200, msg='Failed to create job with single digit hourly repitition interval')
    resultJSON = dict(json.loads(result.get_data(as_text=True)))
    self.assertEqual(resultJSON['repetitionInterval'], 'HOURLY:03')

  def test_getJobHasProperlyFormattedRepititionInterval_wrongorder(self):
    hourly_list_wrong_order = dict(data_simpleJobCreateParams)
    hourly_list_wrong_order['repetitionInterval'] = 'HOURLY:1,3,2'
    result = self.testClient.post('/api/jobs/', data=json.dumps(hourly_list_wrong_order), content_type='application/json')
    self.assertEqual(result.status_code, 200, msg='Failed to create job with hourly repitition interval list in wrong order')
    resultJSON = dict(json.loads(result.get_data(as_text=True)))
    self.assertEqual(resultJSON['repetitionInterval'], 'HOURLY:01,02,03')

  def test_getJobHasProperlyFormattedRepititionInterval_repeat(self):
    hourly_list_repeat = dict(data_simpleJobCreateParams)
    hourly_list_repeat['repetitionInterval'] = 'HOURLY:1,3,2,3,3,3,2,2,1'
    result = self.testClient.post('/api/jobs/', data=json.dumps(hourly_list_repeat), content_type='application/json')
    self.assertEqual(result.status_code, 200, msg='Failed to create job with hourly repitition interval with values repeating')
    resultJSON = dict(json.loads(result.get_data(as_text=True)))
    self.assertEqual(resultJSON['repetitionInterval'], 'HOURLY:01,02,03')

  def test_getJobExecutionsInvalidJob(self):
    result = self.testClient.get('/api/jobs/SomeInvlaidJobKey/execution')
    self.assertEqual(result.status_code, 400, msg='Invalid job key did not return bad request')

  def test_getAndUpdateSuccesfulJobGivesCorrectReturn(self):
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    self.assertEqual(result.status_code, 200)
    resultJSON = json.loads(result.get_data(as_text=True))
    jobGUID = resultJSON['guid']

    #Execute the job
    result2 = self.addExecution(jobGUID, '001_001')
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,1,59,0,pytz.timezone('UTC')))
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,2,59,0,pytz.timezone('UTC')))

    #print(appObj.appData['jobsData'].getJob(jobGUID)._caculatedDict(appObj))

    #Get the job and ensure it's status is Success
    result3 = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(result3.status_code, 200, msg='Read back Job record after it was executed')
    result3JSON = json.loads(result3.get_data(as_text=True))
    result3JSON['lastRunDate'] = None
    result3JSON['lastRunExecutionGUID'] = ""
    expRes = dict(data_simpleJobCreateExpRes)
    expRes['mostRecentCompletionStatus'] = "Success"
    expRes['lastRunReturnCode'] = 0
    self.assertJSONJobStringsEqual(result3JSON, expRes);

    #Update the job and ensure returned data is still Success
    updateNameInput = dict(data_simpleJobCreateParams)
    updateNameInput['name'] = "newJobNamedsffds"
    updateJobNameResult = self.testClient.put('/api/jobs/' + jobGUID, data=json.dumps(updateNameInput), content_type='application/json')
    self.assertEqual(updateJobNameResult.status_code, 200, msg='Put call did not give correct status')
    updateJobNameResultJSON = dict(json.loads(updateJobNameResult.get_data(as_text=True)))
    updateJobNameResultJSON['lastRunDate'] = None
    updateJobNameResultJSON['lastRunExecutionGUID'] = ""
    expRes2 = dict(expRes)
    expRes2['name'] = updateNameInput['name']
    self.assertJSONJobStringsEqual(updateJobNameResultJSON, expRes2);

    #Test get list of jobs returns caculated fields
    result3 = self.testClient.get('/api/jobs/')
    self.assertEqual(result3.status_code, 200, msg='Fetch all jobs failed')
    result3JSON = json.loads(result3.get_data(as_text=True))
    expPaginationResult = {'offset': 0, 'pagesize': 100, 'total': 1}
    self.assertJSONStringsEqual(result3JSON["pagination"], expPaginationResult);
    self.assertEqual(len(result3JSON["result"]),1,msg="Wrong number of returned results")
    result3JSON["result"][0]['lastRunDate'] = None
    result3JSON["result"][0]['lastRunExecutionGUID'] = ""
    self.assertJSONJobStringsEqual(result3JSON["result"][0], expRes2);

    #Go 1 year into the future
    curDateTime = appObj.getCurDateTime()
    appObj.setTestingDateTime(curDateTime + relativedelta(years=1))
    
    #print(appObj.appData['jobsData'].getJob(jobGUID)._caculatedDict(appObj))
    
    #Get the job and ensure it's status is now Unknown
    resultFutureGet = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(resultFutureGet.status_code, 200, msg='Read back record 1 year in future')
    resultFutureGetJSON = json.loads(resultFutureGet.get_data(as_text=True))
    resultFutureGetJSON['lastRunDate'] = None
    resultFutureGetJSON['lastRunExecutionGUID'] = ""
    expRes3 = dict(expRes2)
    expRes3['mostRecentCompletionStatus'] = "Unknown"
    self.assertJSONJobStringsEqual(resultFutureGetJSON, expRes3);

    #Go back to today
    appObj.setTestingDateTime(None)

    #Test job delete returns mostREcentCompletionStatus Success
    result4 = self.testClient.delete('/api/jobs/' + jobGUID)
    self.assertEqual(result4.status_code, 200, msg='Didn''t delete Job')
    result4JSON = json.loads(result4.get_data(as_text=True))
    result4JSON['lastRunDate'] = None
    result4JSON['lastRunExecutionGUID'] = ""
    self.assertJSONJobStringsEqual(result4JSON, expRes2);

  def test_getAndUpdateFailedJobGivesCorrectReturn(self):
    data_simpleJobCreateParamsFailed = dict(data_simpleJobCreateParams)
    data_simpleJobCreateParamsFailed['command'] = 'badCommand'
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParamsFailed), content_type='application/json')
    self.assertEqual(result.status_code, 200)
    resultJSON = json.loads(result.get_data(as_text=True))
    jobGUID = resultJSON['guid']

    #Execute the job
    result2 = self.addExecution(jobGUID, '001_001')
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,1,59,0,pytz.timezone('UTC')))
    appObj.jobExecutor.loopIteration(datetime.datetime(2016,1,5,14,2,59,0,pytz.timezone('UTC')))

    #print(appObj.appData['jobsData'].getJob(jobGUID)._caculatedDict(appObj))

    #Get the job and ensure it's status is Fail
    result3 = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(result3.status_code, 200, msg='Read back Job record after it was executed')
    result3JSON = json.loads(result3.get_data(as_text=True))
    result3JSON['lastRunDate'] = None
    result3JSON['lastRunExecutionGUID'] = ""
    expRes = dict(data_simpleJobCreateExpRes)
    expRes['mostRecentCompletionStatus'] = "Fail"
    expRes['command'] = data_simpleJobCreateParamsFailed['command']
    expRes['lastRunReturnCode'] = 127
    self.assertJSONJobStringsEqual(result3JSON, expRes);

    #Update the job and ensure returned data is still Fail
    updateNameInput = dict(data_simpleJobCreateParamsFailed)
    updateNameInput['name'] = "newJobNamedsffds"
    updateJobNameResult = self.testClient.put('/api/jobs/' + jobGUID, data=json.dumps(updateNameInput), content_type='application/json')
    self.assertEqual(updateJobNameResult.status_code, 200, msg='Put call did not give correct status')
    updateJobNameResultJSON = dict(json.loads(updateJobNameResult.get_data(as_text=True)))
    updateJobNameResultJSON['lastRunDate'] = None
    updateJobNameResultJSON['lastRunExecutionGUID'] = ""
    expRes2 = dict(expRes)
    expRes2['name'] = updateNameInput['name']
    self.assertJSONJobStringsEqual(updateJobNameResultJSON, expRes2);

    #Test get list of jobs returns caculated fields
    result3 = self.testClient.get('/api/jobs/')
    self.assertEqual(result3.status_code, 200, msg='Fetch all jobs failed')
    result3JSON = json.loads(result3.get_data(as_text=True))
    expPaginationResult = {'offset': 0, 'pagesize': 100, 'total': 1}
    self.assertJSONStringsEqual(result3JSON["pagination"], expPaginationResult);
    self.assertEqual(len(result3JSON["result"]),1,msg="Wrong number of returned results")
    result3JSON["result"][0]['lastRunDate'] = None
    result3JSON["result"][0]['lastRunExecutionGUID'] = ""
    self.assertJSONJobStringsEqual(result3JSON["result"][0], expRes2);

    #Go 1 year into the future
    curDateTime = appObj.getCurDateTime()
    appObj.setTestingDateTime(curDateTime + relativedelta(years=1))
    
    #print(appObj.appData['jobsData'].getJob(jobGUID)._caculatedDict(appObj))
    
    #Get the job and ensure it's status is now Unknown
    resultFutureGet = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(resultFutureGet.status_code, 200, msg='Read back record 1 year in future')
    resultFutureGetJSON = json.loads(resultFutureGet.get_data(as_text=True))
    resultFutureGetJSON['lastRunDate'] = None
    resultFutureGetJSON['lastRunExecutionGUID'] = ""
    expRes3 = dict(expRes2)
    expRes3['mostRecentCompletionStatus'] = "Unknown"
    self.assertJSONJobStringsEqual(resultFutureGetJSON, expRes3);

    #Go back to today
    appObj.setTestingDateTime(None)

    #Test job delete returns mostRecentCompletionStatus Fail
    result4 = self.testClient.delete('/api/jobs/' + jobGUID)
    self.assertEqual(result4.status_code, 200, msg='Didn''t delete Job')
    result4JSON = json.loads(result4.get_data(as_text=True))
    result4JSON['lastRunDate'] = None
    result4JSON['lastRunExecutionGUID'] = ""
    self.assertJSONJobStringsEqual(result4JSON, expRes2);

  def test_pinAndUnpinJob(self):
    result = self.testClient.post('/api/jobs/', data=json.dumps(data_simpleJobCreateParams), content_type='application/json')
    resultJSON = dict(json.loads(result.get_data(as_text=True)))
    self.assertEqual(result.status_code, 200, msg='First job creation should have worked')
    jobGUID = resultJSON['guid']
    origName = resultJSON['name']
    self.assertEqual(resultJSON['pinned'],False)

    #Read back job to make sure it starts unpinned
    result2 = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(result2.status_code, 200, msg='Read back record')
    result2JSON = dict(json.loads(result2.get_data(as_text=True)))
    self.assertEqual(resultJSON['pinned'],False)

    #Update pinned to true
    updateInput = dict(data_simpleJobCreateParams)
    updateInput['pinned'] = True
    updateJobNameResult = self.testClient.put('/api/jobs/' + jobGUID, data=json.dumps(updateInput), content_type='application/json')
    self.assertEqual(updateJobNameResult.status_code, 200, msg='Put call did not give correct status')
    updateJobResultJSON = dict(json.loads(updateJobNameResult.get_data(as_text=True)))
    self.assertEqual(updateJobResultJSON['pinned'],True)

    #Test get returns correct value
    result2 = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(result2.status_code, 200, msg='Read back record')
    result2JSON = dict(json.loads(result2.get_data(as_text=True)))
    self.assertEqual(result2JSON['pinned'],True)

    #Update pinned to false
    update2Input = dict(data_simpleJobCreateParams)
    update2Input['pinned'] = False
    updateJob2Result = self.testClient.put('/api/jobs/' + jobGUID, data=json.dumps(update2Input), content_type='application/json')
    self.assertEqual(updateJob2Result.status_code, 200, msg='Put call did not give correct status')
    updateJob2ResultJSON = dict(json.loads(updateJob2Result.get_data(as_text=True)))
    self.assertEqual(updateJob2ResultJSON['pinned'],False)

    result3 = self.testClient.get('/api/jobs/' + jobGUID)
    self.assertEqual(result3.status_code, 200, msg='Read back record')
    result3JSON = dict(json.loads(result3.get_data(as_text=True)))
    self.assertEqual(result3JSON['pinned'],False)

  def test_createPinnedJob(self):
    jc = dict(data_simpleJobCreateParams)
    jc['pinned'] = True
    result = self.testClient.post('/api/jobs/', data=json.dumps(jc), content_type='application/json')
    resultJSON = dict(json.loads(result.get_data(as_text=True)))
    self.assertEqual(result.status_code, 200, msg='First job creation should have worked')
    jobGUID = resultJSON['guid']
    origName = resultJSON['name']
    self.assertEqual(resultJSON['pinned'],True)


