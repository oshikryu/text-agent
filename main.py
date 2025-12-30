import os
import googlemaps
from openai import OpenAI
from prompt_toolkit import prompt
from dotenv import load_dotenv


# should be a separate model/Class
patient_info = dict(
  patient_id=22,
  first_name= "",
  last_name="",
  dob= "",
  gender= "",
  address= "",
  phone= "",
  allergies= "",
  prescriptions= "",
)

insurance_info = dict(
  payer_name="",
  insurance_id="", # optional field
)

SCHEDULE_STATUS = {
  "confirmed": "confirmed",
  "requested": "requested",
  "cancelled": "cancelled"
}

appointment_request = dict(
  patient_id=None,
  provider_id=None,
  start_time=None,
  appointment_length=0,
  reason_for_visit="",
  schedule_status=SCHEDULE_STATUS.get('requested')
)

# TODO: generate mock data for providers
providers_list = [

]

# TODO: maybe make the user response a dict where we have key -> value
# actual response instead of zipping a 1 to 1 array of key/values
CLI_STEPS = [
  {
    "data_structure": "patient_info",
    "fields": ["first_name", "last_name", "dob", "gender"],
    "user_response": []
  },
  {
    "data_structure": "appointment_request",
    "fields": ["reason_for_visit"],
    "user_response": []
  },
  {
    "data_structure": "patient_info",
    "fields": ["allergies", "medications"],
    "user_response": []
  },
  {
    "data_structure": "patient_info",
    "fields": ["address"],
    "user_response": []
  },
  {
    "data_structure": "insurance_info",
    "fields": ["payer_name", "insurance_id"],
    "user_response": []
  },
]

"""
map keys to a CLI friendly display text
"""
display_map = {
  "first_name": "First Name",
  "last_name": "Last Name",
  "dob": "Date of Birth",
  "gender": "Gender",
  "reason_for_visit": "Reason for Visit",
  "allergies": "Allergies",
  "medications": "Medications",
  "address": "Address",
  "payer_name": "Insurance Payer Name",
  "insurance_id": "Insurance ID (Optional)",
}


"""
Should be an intermediate state that can be edited in memory before actually persisting in db
"""
def save_valid_state(data_structure, field, answer):
  match data_structure:
    case "patient_info":
      patient_info[field] = answer
    case "appointment_request":
      appointment_request[field] = answer
    case "insurance_info":
      insurance_info[field] = answer

def mapped_prompt_display(key):
  match key:
    case "first_name" | "last_name" | "dob" | "gender" | "address" | "payer_name" | "insurance_id":
      return f"What is your {display_map[key]}?: "
    case "reason_for_visit":
      return f"What is your {display_map[key]}?: "
    case "allergies":
      return f"Do you have any {display_map[key]}? (enter 'none' if no allergies): "
    case "medications":
      return f"Are you currently taking any {display_map[key]}? (enter 'none' if no medications): "
    case _:
      return f"Please provide {key}: "

def extract_value_from_llm_output(wrapper, field, value):
  match field:
    case "dob":
      prompt = """
          Does the format include month, date and year? Return invalid if not.

          Format date of birth based on (MMDDYYYY format)
      """
      res = wrapper.query(prompt, value)
      # Parse the async response to extract the actual content
      llm_response = res.output_text
      return llm_response
    case "address":
      prompt = f"""
      The provided address you gave was not found: {value}
      Provide a response to prompt the user for another address
      """
      res = wrapper.query(prompt, value)
      llm_response = res.output_text
      return llm_response
    case _:
      return value

def normalize_user_input(wrapper, field, value):
  match field:
    case "dob":
      # TODO: need to sanitize the field before passing to openai input
      prompt = f"Get my date of birth based on the following input"
      res = wrapper.query(prompt, value)
      llm_response = res.output_text
      return llm_response
    case _:
      # Default normalization for other fields
      return value

def init():
  if __name__ == '__main__':
    wrapper = LLMWrapper()
    fieldValidators = FieldValidators()

    for idx, step in enumerate(CLI_STEPS):
      data_structure = step.get('data_structure')

      fields_in_progress = 0
      while fields_in_progress < len(step.get('fields')):
        field = step.get('fields')[fields_in_progress]

        # Validation loop: keep asking until valid input is provided
        while True:
          answer = prompt(mapped_prompt_display(field))

          normalized_value = normalize_user_input(wrapper, field, answer)
          extracted_value = extract_value_from_llm_output(wrapper, field, answer)
          is_valid = fieldValidators.is_field_valid(field, extracted_value)

          if is_valid:
            # Save the valid answer and move to next field
            step['user_response'].append(extracted_value)


            save_valid_state(data_structure, field, extracted_value)
            fields_in_progress += 1
            break
          else:
            print(normalized_value)


    # call the appointment request service
    # return the appointment request
    return AppointmentRequestService.create_appointment(patient_info, appointment_request)

    # wait for provider confirmation

class FieldValidators():
  # TODO: add try/catch for gmaps client key
  def __init__(self):
    load_dotenv()
    GMAPS_KEY = os.getenv('GMAPS_KEY')
    self.gmaps_client = googlemaps.Client(
        key=GMAPS_KEY,
    )

  def get_address_validation(self, address): 
    # TODO: re-prompt address validation?
    return self.gmaps_client.addressvalidation([address])

  def is_field_valid(self, key, val):
    match key:
      case "first_name" | "last_name":
        # TODO:
        # basic validation like trimming white text, valid characters for storage
        # edge cases like taking into account Jr. other non alphanumeric
        return val != ""
      case "dob":
        # check for normalized dob e.g. 01012002 (MMDDYYYY format)
        if len(val) != 8:
          return False
        if not val.isdigit():
          return False
        # Basic range validation for month and day
        month = int(val[0:2])
        day = int(val[2:4])
        if month < 1 or month > 12:
          return False
        if day < 1 or day > 31:
          return False
        return True
      case "gender":
        # Accept common gender values (case insensitive)
        valid_genders = ["male", "female", "other", "prefer not to say"]
        return val.lower().strip() in valid_genders
      case "reason_for_visit":
        # Required field, must have some content
        return val.strip() != ""
      case "allergies" | "medications":
        # Accept "none" or any non-empty value
        return val.strip() != ""
      case "address":
        return self.get_address_validation(val)
      case "payer_name":
        # Insurance payer name is required
        return val.strip() != ""
      case "insurance_id":
        # Optional field - always valid
        return True
      case _:
        # Default validation for other fields
        return val != ""



class LLMWrapper():
  def __init__(self):
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    self.client = OpenAI(
        api_key=OPENAI_API_KEY,
    )

  def query(self, instructions, input):
      try:
          return self.client.responses.create(
            # TODO: make this model configurable
            model="gpt-4o",
            instructions=instructions,
            input=input,
          )
      except Exception as e:
          print(f"Error querying LLM: {e}")
          return None

class AppointmentRequestService():
  @staticmethod
  def create_appointment(patient_info, appointment_request):
    """
    Creates an appointment request with patient info
    Returns the appointment request object
    """
    # Set patient_id from patient_info
    appointment_request['patient_id'] = patient_info.get('patient_id')
    appointment_request['schedule_status'] = SCHEDULE_STATUS.get('requested')

    # TODO: Persist to database
    # TODO: Send confirmation to patient

    return appointment_request

  @staticmethod
  def confirm_appointment(appointment_request):
    """
    Confirms an appointment request
    Updates schedule_status to confirmed
    """
    appointment_request['schedule_status'] = SCHEDULE_STATUS.get('confirmed')

    # TODO: Update in database
    # TODO: Send confirmation notification

    return appointment_request

  @staticmethod
  def cancel_appointment(appointment_request):
    """
    Cancels an appointment
    Updates schedule_status to cancelled
    """
    appointment_request['schedule_status'] = SCHEDULE_STATUS.get('cancelled')

    # TODO: Update in database
    # TODO: Send cancellation notification

    return appointment_request

  @staticmethod
  def assign_provider(appointment_request, provider_id):
    """
    Assigns a provider to the appointment
    """
    appointment_request['provider_id'] = provider_id

    # TODO: Update in database
    # TODO: Notify provider

    return appointment_request


class ProviderMatchingService():
  def get_relevant_providers():
    pass

  def get_provider_open_schedule():
    pass

  def get_all_provider_schedules():
    pass

init()
