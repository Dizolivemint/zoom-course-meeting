SELECT DISTINCT cs.code
,cs.Descrip as longname 
,RTRIM(CS.Code) + '.' + RTRIM(CS.Section) + '.' + RTRIM(t.Code) + '.' + RTRIM(SC.Code) AS shortname
,REPLACE(CONVERT(varchar, IIF(sc.code = 'NY', CAST(cs.StartDate AS DATETIME), CAST(aca.Date as DATETIME)) + CAST(RIGHT(CAST(csd.StartTime AS varchar), 7) AS DATETIME), 121), ' ', 'T') + 'Z' as start_time
,csd.LengthMinutes as duration
,ss.email as schedule_for
,IIF(sc.code = 'CH', 'America/Chicago', 
	IIF(sc.code = 'NY', 'America/New_York', 'America/Los_Angeles')) AS timezone
,IIF(cs.DaysFlag > 0, FLOOR(LOG(cs.DaysFlag) / LOG(2)) + 1, 0) as weekly_days
,CAST(CAST(cs.EndDate AS DATE) AS VARCHAR) + 'T' + '23:59:59Z' AS end_date_time
FROM [dbo].[AdClassSched] cs
INNER JOIN [dbo].[AdClassSchedDay] csd ON cs.AdClassSchedID = csd.AdClassSchedID
INNER JOIN [dbo].[AdClassSchedTerm] st ON cs.AdClassSchedID = st.AdClassSchedID
INNER JOIN [dbo].[AdTerm] t ON t.AdTermID = st.AdTermID
INNER JOIN [dbo].[SyStaff] ss ON cs.AdTeacherID = ss.SyStaffID
INNER JOIN [dbo].[AdCatalogYearCourse] acyc ON cs.AdCourseID = acyc.AdCourseID
INNER JOIN [dbo].[AdCatalogYear] acy ON acyc.AdCatalogYearID = acy.AdCatalogYearID
INNER JOIN SyCampus AS SC ON CS.SyCampusID = SC.SyCampusID
CROSS APPLY (SELECT TOP 1 [Date], AdClassSchedID from [dbo].[AdClassAttend] where cs.AdClassSchedID = AdClassSchedID) aca
WHERE cs.Active = 1
AND st.AdTermID = 56
/* Uncomment for electives
AND NOT EXISTS (
    SELECT AdCourseID FROM [dbo].[AdProgramCourse]
    WHERE  cs.AdCourseID = AdCourseID
)
*/
ORDER BY cs.Code