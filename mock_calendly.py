"""
Mock Calendly API Implementation
Simulates Calendly API endpoints for appointment scheduling
"""

import json
import os
from datetime import datetime, timedelta, time as dt_time
from typing import List, Dict, Optional
import uuid
from pathlib import Path

from schemas import (
    AppointmentRequest,
    AppointmentResponse,
    AvailabilityRequest,
    AvailabilityResponse,
    TimeSlot,
    APPOINTMENT_TYPES
)


class MockCalendlyAPI:
    """Mock implementation of Calendly API"""
    
    def __init__(self, appointments_file: str = "data/appointments.json"):
        self.appointments_file = appointments_file
        self._ensure_appointments_file()
        
    def _ensure_appointments_file(self):
        """Ensure appointments file exists"""
        os.makedirs(os.path.dirname(self.appointments_file), exist_ok=True)
        if not os.path.exists(self.appointments_file):
            with open(self.appointments_file, 'w') as f:
                json.dump({"appointments": []}, f)
    
    def _load_appointments(self) -> List[Dict]:
        """Load existing appointments"""
        try:
            with open(self.appointments_file, 'r') as f:
                data = json.load(f)
                return data.get("appointments", [])
        except Exception as e:
            print(f"Error loading appointments: {e}")
            return []
    
    def _save_appointments(self, appointments: List[Dict]):
        """Save appointments to file"""
        try:
            with open(self.appointments_file, 'w') as f:
                json.dump({"appointments": appointments}, f, indent=2)
        except Exception as e:
            print(f"Error saving appointments: {e}")
    
    def get_availability(self, request: AvailabilityRequest) -> AvailabilityResponse:
        """
        Get available time slots for a specific date and appointment type
        
        Args:
            request: AvailabilityRequest with date and appointment_type
            
        Returns:
            AvailabilityResponse with available slots
        """
        try:
            # Parse the requested date
            req_date = datetime.strptime(request.date, "%Y-%m-%d").date()
            
            # Check if date is in the past
            if req_date < datetime.now().date():
                return AvailabilityResponse(
                    date=request.date,
                    appointment_type=request.appointment_type,
                    available_slots=[],
                    total_slots=0
                )
            
            # Check if it's a weekend
            if req_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return AvailabilityResponse(
                    date=request.date,
                    appointment_type=request.appointment_type,
                    available_slots=[],
                    total_slots=0
                )
            
            # Get appointment duration
            duration = APPOINTMENT_TYPES[request.appointment_type]["duration"]
            
            # Generate time slots (9 AM to 5 PM)
            business_start = dt_time(9, 0)
            business_end = dt_time(17, 0)
            
            # Load existing appointments for this date
            existing_appointments = self._load_appointments()
            booked_slots = [
                (appt["start_time"], appt["end_time"])
                for appt in existing_appointments
                if appt["date"] == request.date and appt["status"] == "confirmed"
            ]
            
            # Generate all possible slots
            available_slots = []
            current_time = datetime.combine(req_date, business_start)
            end_time = datetime.combine(req_date, business_end)
            
            while current_time + timedelta(minutes=duration) <= end_time:
                slot_start = current_time.strftime("%H:%M")
                slot_end = (current_time + timedelta(minutes=duration)).strftime("%H:%M")
                
                # Check if slot overlaps with any booked appointment
                is_available = not any(
                    self._slots_overlap(slot_start, slot_end, booked_start, booked_end)
                    for booked_start, booked_end in booked_slots
                )
                
                # If it's today, check if the time has already passed
                if req_date == datetime.now().date():
                    current_hour = datetime.now().hour
                    current_minute = datetime.now().minute
                    slot_hour, slot_minute = map(int, slot_start.split(':'))
                    
                    if (slot_hour < current_hour) or (slot_hour == current_hour and slot_minute <= current_minute):
                        is_available = False
                
                available_slots.append(
                    TimeSlot(
                        start_time=slot_start,
                        end_time=slot_end,
                        available=is_available
                    )
                )
                
                # Move to next slot (15-minute increments)
                current_time += timedelta(minutes=15)
            
            # Filter to only available slots
            available_only = [slot for slot in available_slots if slot.available]
            
            return AvailabilityResponse(
                date=request.date,
                appointment_type=request.appointment_type,
                available_slots=available_only,
                total_slots=len(available_only)
            )
            
        except Exception as e:
            print(f"Error getting availability: {e}")
            return AvailabilityResponse(
                date=request.date,
                appointment_type=request.appointment_type,
                available_slots=[],
                total_slots=0
            )
    
    def _slots_overlap(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        """Check if two time slots overlap"""
        # Convert to minutes since midnight for easier comparison
        def time_to_minutes(t: str) -> int:
            h, m = map(int, t.split(':'))
            return h * 60 + m
        
        s1 = time_to_minutes(start1)
        e1 = time_to_minutes(end1)
        s2 = time_to_minutes(start2)
        e2 = time_to_minutes(end2)
        
        # Check overlap: start1 < end2 and start2 < end1
        return s1 < e2 and s2 < e1
    
    def book_appointment(self, request: AppointmentRequest) -> AppointmentResponse:
        """
        Book an appointment
        
        Args:
            request: AppointmentRequest with all booking details
            
        Returns:
            AppointmentResponse with confirmation
        """
        try:
            # Validate the date
            req_date = datetime.strptime(request.appointment_date, "%Y-%m-%d").date()
            
            if req_date < datetime.now().date():
                return AppointmentResponse(
                    booking_id="",
                    status="failed",
                    confirmation_code="",
                    appointment_type=request.appointment_type,
                    date=request.appointment_date,
                    start_time=request.start_time,
                    end_time="",
                    patient_name=request.patient.name,
                    patient_email=request.patient.email,
                    reason="Cannot book appointments in the past",
                    created_at=datetime.now().isoformat()
                )
            
            # Check if weekend
            if req_date.weekday() >= 5:
                return AppointmentResponse(
                    booking_id="",
                    status="failed",
                    confirmation_code="",
                    appointment_type=request.appointment_type,
                    date=request.appointment_date,
                    start_time=request.start_time,
                    end_time="",
                    patient_name=request.patient.name,
                    patient_email=request.patient.email,
                    reason="Clinic is closed on weekends",
                    created_at=datetime.now().isoformat()
                )
            
            # Calculate end time
            duration = APPOINTMENT_TYPES[request.appointment_type]["duration"]
            start_dt = datetime.strptime(request.start_time, "%H:%M")
            end_dt = start_dt + timedelta(minutes=duration)
            end_time = end_dt.strftime("%H:%M")
            
            # Check availability
            availability_req = AvailabilityRequest(
                date=request.appointment_date,
                appointment_type=request.appointment_type
            )
            availability = self.get_availability(availability_req)
            
            # Verify the requested slot is available
            is_slot_available = any(
                slot.start_time == request.start_time and slot.available
                for slot in availability.available_slots
            )
            
            if not is_slot_available:
                return AppointmentResponse(
                    booking_id="",
                    status="failed",
                    confirmation_code="",
                    appointment_type=request.appointment_type,
                    date=request.appointment_date,
                    start_time=request.start_time,
                    end_time=end_time,
                    patient_name=request.patient.name,
                    patient_email=request.patient.email,
                    reason="Time slot is not available",
                    created_at=datetime.now().isoformat()
                )
            
            # Generate booking details
            booking_id = f"APPT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            confirmation_code = str(uuid.uuid4())[:6].upper()
            
            # Create appointment record
            appointment = {
                "booking_id": booking_id,
                "confirmation_code": confirmation_code,
                "status": "confirmed",
                "appointment_type": request.appointment_type,
                "date": request.appointment_date,
                "start_time": request.start_time,
                "end_time": end_time,
                "duration_minutes": duration,
                "patient": {
                    "name": request.patient.name,
                    "email": request.patient.email,
                    "phone": request.patient.phone
                },
                "reason": request.reason,
                "created_at": datetime.now().isoformat()
            }
            
            # Save appointment
            appointments = self._load_appointments()
            appointments.append(appointment)
            self._save_appointments(appointments)
            
            return AppointmentResponse(
                booking_id=booking_id,
                status="confirmed",
                confirmation_code=confirmation_code,
                appointment_type=request.appointment_type,
                date=request.appointment_date,
                start_time=request.start_time,
                end_time=end_time,
                patient_name=request.patient.name,
                patient_email=request.patient.email,
                reason=request.reason,
                created_at=appointment["created_at"]
            )
            
        except Exception as e:
            print(f"Error booking appointment: {e}")
            return AppointmentResponse(
                booking_id="",
                status="failed",
                confirmation_code="",
                appointment_type=request.appointment_type,
                date=request.appointment_date,
                start_time=request.start_time,
                end_time="",
                patient_name=request.patient.name,
                patient_email=request.patient.email,
                reason=f"Booking failed: {str(e)}",
                created_at=datetime.now().isoformat()
            )
    
    def get_booking(self, booking_id: str) -> Optional[Dict]:
        """Get booking details by ID"""
        appointments = self._load_appointments()
        for appt in appointments:
            if appt["booking_id"] == booking_id:
                return appt
        return None
    
    def cancel_appointment(self, booking_id: str) -> bool:
        """Cancel an appointment"""
        try:
            appointments = self._load_appointments()
            for appt in appointments:
                if appt["booking_id"] == booking_id:
                    appt["status"] = "cancelled"
                    self._save_appointments(appointments)
                    return True
            return False
        except Exception as e:
            print(f"Error cancelling appointment: {e}")
            return False


# Global instance
calendly_api = MockCalendlyAPI()
