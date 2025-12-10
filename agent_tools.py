"""
LangChain Tools for the Appointment Scheduling Agent
"""

from typing import Optional, Dict, Any
from langchain.tools import BaseTool
from pydantic import Field
from datetime import datetime

from mock_calendly import calendly_api
from schemas import (
    AvailabilityRequest,
    AppointmentRequest,
    PatientInfo
)
from faq_rag import get_rag_system


class CheckAvailabilityTool(BaseTool):
    """Tool to check available appointment slots"""
    
    name: str = "check_availability"
    description: str = """
    Check available appointment time slots for a specific date and appointment type.
    
    Use this tool when you need to find available times for an appointment.
    
    Args:
        date: Date in YYYY-MM-DD format (e.g., "2024-01-15")
        appointment_type: One of: "general_consultation", "follow_up", "physical_exam", "specialist_consultation"
    
    Returns:
        A dictionary with available time slots and total count
    """
    
    def _run(self, date: str, appointment_type: str) -> str:
        """Check availability for a given date and appointment type"""
        try:
            # Validate appointment type
            valid_types = ["general_consultation", "follow_up", "physical_exam", "specialist_consultation"]
            if appointment_type not in valid_types:
                return f"Error: Invalid appointment type. Must be one of: {', '.join(valid_types)}"
            
            # Validate date format
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return "Error: Date must be in YYYY-MM-DD format (e.g., 2024-01-15)"
            
            # Check availability
            request = AvailabilityRequest(
                date=date,
                appointment_type=appointment_type
            )
            
            response = calendly_api.get_availability(request)
            
            if response.total_slots == 0:
                # Check if it's a weekend
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                if date_obj.weekday() >= 5:
                    return f"No slots available on {date}. The clinic is closed on weekends. Please choose a weekday (Monday-Friday)."
                
                # Check if it's in the past
                if date_obj.date() < datetime.now().date():
                    return f"No slots available on {date}. This date is in the past. Please choose a future date."
                
                return f"No slots available on {date}. The date is fully booked. Would you like to check another date?"
            
            # Format the response
            slots_text = []
            for slot in response.available_slots[:10]:  # Limit to first 10 slots
                # Convert 24-hour to 12-hour format
                start_time = datetime.strptime(slot.start_time, "%H:%M")
                formatted_time = start_time.strftime("%I:%M %p").lstrip("0")
                slots_text.append(formatted_time)
            
            result = f"Available slots on {date} for {appointment_type.replace('_', ' ')}:\n"
            result += "\n".join(f"- {time}" for time in slots_text)
            result += f"\n\nTotal available slots: {response.total_slots}"
            
            return result
            
        except Exception as e:
            return f"Error checking availability: {str(e)}"
    
    async def _arun(self, date: str, appointment_type: str) -> str:
        """Async version"""
        return self._run(date, appointment_type)


class BookAppointmentTool(BaseTool):
    """Tool to book an appointment"""
    
    name: str = "book_appointment"
    description: str = """
    Book a medical appointment with patient details.
    
    Use this tool ONLY after:
    1. Confirming the appointment type, date, and time with the patient
    2. Collecting all required patient information
    3. Getting final confirmation from the patient
    
    Required args:
        patient_name: Patient's full name
        patient_email: Patient's email address
        patient_phone: Patient's phone number
        appointment_type: One of: "general_consultation", "follow_up", "physical_exam", "specialist_consultation"
        appointment_date: Date in YYYY-MM-DD format
        start_time: Start time in HH:MM format (24-hour, e.g., "14:00" for 2:00 PM)
        reason: Brief reason for the visit
    
    Returns:
        Confirmation details including booking ID and confirmation code
    """
    
    def _run(
        self,
        patient_name: str,
        patient_email: str,
        patient_phone: str,
        appointment_type: str,
        appointment_date: str,
        start_time: str,
        reason: str
    ) -> str:
        """Book an appointment"""
        try:
            # Validate required fields
            if not all([patient_name, patient_email, patient_phone, appointment_type, 
                       appointment_date, start_time, reason]):
                return "Error: All fields are required to book an appointment."
            
            # Create patient info
            try:
                patient = PatientInfo(
                    name=patient_name,
                    email=patient_email,
                    phone=patient_phone
                )
            except Exception as e:
                return f"Error: Invalid patient information - {str(e)}"
            
            # Create booking request
            request = AppointmentRequest(
                appointment_type=appointment_type,
                appointment_date=appointment_date,
                start_time=start_time,
                patient=patient,
                reason=reason
            )
            
            # Book the appointment
            response = calendly_api.book_appointment(request)
            
            if response.status == "failed":
                return f"Booking failed: {response.reason}"
            
            # Format success response
            start_dt = datetime.strptime(start_time, "%H:%M")
            formatted_time = start_dt.strftime("%I:%M %p").lstrip("0")
            
            date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
            
            result = f"""✅ Appointment Successfully Booked!

Confirmation Details:
- Booking ID: {response.booking_id}
- Confirmation Code: {response.confirmation_code}
- Patient: {patient_name}
- Type: {appointment_type.replace('_', ' ').title()}
- Date: {formatted_date}
- Time: {formatted_time}
- Duration: {response.end_time}
- Reason: {reason}

A confirmation email has been sent to {patient_email}.

Important Reminders:
- Please arrive 15 minutes early to complete any necessary paperwork
- Bring your insurance card and photo ID
- If you need to cancel or reschedule, please call us at least 24 hours in advance at +1-555-123-4567
"""
            
            return result
            
        except Exception as e:
            return f"Error booking appointment: {str(e)}"
    
    async def _arun(
        self,
        patient_name: str,
        patient_email: str,
        patient_phone: str,
        appointment_type: str,
        appointment_date: str,
        start_time: str,
        reason: str
    ) -> str:
        """Async version"""
        return self._run(
            patient_name, patient_email, patient_phone,
            appointment_type, appointment_date, start_time, reason
        )


class SearchFAQTool(BaseTool):
    """Tool to search clinic FAQ knowledge base"""
    
    name: str = "search_faq"
    description: str = """
    Search the clinic's knowledge base to answer questions about:
    - Clinic location, hours, and directions
    - Insurance and billing
    - What to bring to appointments
    - Clinic policies (cancellation, late arrival, etc.)
    - COVID-19 protocols
    - Services offered
    - And more
    
    Use this tool when the patient asks questions about the clinic, policies, or services.
    
    Args:
        question: The patient's question
    
    Returns:
        Relevant information from the knowledge base
    """
    
    rag_system: Any = Field(default_factory=get_rag_system)
    
    def _run(self, question: str) -> str:
        """Search FAQ knowledge base"""
        try:
            # Get relevant context
            context = self.rag_system.get_context_for_query(question, n_results=3)
            
            if context == "No relevant information found in the knowledge base.":
                return """I don't have specific information about that in my knowledge base. 
For the most accurate and up-to-date information, I recommend:
- Calling our office at +1-555-123-4567
- Visiting our website at www.healthcareplus.com
- Emailing us at info@healthcareplus.com

Is there anything else I can help you with, or would you like to schedule an appointment?"""
            
            return context
            
        except Exception as e:
            return f"I'm having trouble accessing that information right now. Please call our office at +1-555-123-4567 for assistance."
    
    async def _arun(self, question: str) -> str:
        """Async version"""
        return self._run(question)


# Create tool instances
def get_agent_tools():
    """Get all agent tools"""
    return [
        CheckAvailabilityTool(),
        BookAppointmentTool(),
        SearchFAQTool()
    ]
