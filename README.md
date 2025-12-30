# CLI Text Agent

## Project CLI loop

Part I
- user prompt
- validation of input
- LLM integration here?
- store in dict/model

- determine if we can go to the next step
-
- Patient info
- Insurance info
- Medical info (allergies, current medications)
- reason for visit
- Demographics (gender, DOB, address)?

- Submit info and wait for appointment selection response


Part II

Filter providers based on insurance and specialty

present appointment times + relevant providers

(mock data)
- provider
- specialty
- schedule windows
-

Select appointment times
patient + provider id, time start, appointment length (15 min, 30 min)

Returns an array of possible times

Part III
Appointment Request
Patient requests with provider
(This is the step 6 confirmation)
Shows patient info, potential assigned physician, and date/time

Part IV
Provider confirms appointment
patient notified of appointment


## Database models:

Patient
- first
- last
- DOB
- gender
- allergies
- prescriptions
- insurance info (TBD break out into separate table?)
- address

Insurance
- payer name
- group id/insurance id
-

Appointment Request
- patient_id
- start_time
- appointment length (in minutes)
- reason for visit
- schedule_status (ENUM confirmed, requested, cancelled,...?)
- provider_id ()

Provider
- first
- last
- gender
- DOB
- NPI?
- specialty
- schedule blocks (Day of week, times as integer representations?) 



# Future todo:
- allow  back/forth in the conversation steps (stack pop, etc)
- tests
