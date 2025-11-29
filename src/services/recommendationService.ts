// src/services/recommendationService.ts
import { apiClient } from '@/lib/api'

export interface Doctor {
  id: string
  name: string
  specialization: string
  experience: number
  rating: number
  reviews: number
  fees: number
  hospital: string
  locality: string
  lat?: number | null
  lon?: number | null
  image: string
  profile_link: string
  score?: number
}

/**
 * Search for doctors by city and specialization
 */
export async function searchDoctors(
  city: string,
  specialization: string,
  pages: number = 2
): Promise<Doctor[]> {
  try {
    const response = await apiClient.get('/recommendations', {
      params: {
        city,
        query: specialization,
        pages
      }
    })
    return response.data || []
  } catch (error) {
    console.error('Error searching doctors:', error)
    throw error
  }
}

/**
 * Get top recommended doctors
 */
export async function getTopDoctors(
  city: string,
  specialization: string
): Promise<Doctor | null> {
  try {
    const doctors = await searchDoctors(city, specialization, 1)
    return doctors.length > 0 ? doctors[0] : null
  } catch (error) {
    console.error('Error getting top doctor:', error)
    return null
  }
}

/**
 * Get doctors by specialty with filters
 */
export async function getDoctorsBySpecialty(
  city: string,
  specialty: string,
  maxFees?: number,
  minExperience?: number,
  minRating?: number
): Promise<Doctor[]> {
  try {
    const doctors = await searchDoctors(city, specialty, 3)
    
    // Client-side filtering
    return doctors.filter(doc => {
      if (maxFees && doc.fees > maxFees) return false
      if (minExperience && doc.experience < minExperience) return false
      if (minRating && doc.rating < minRating) return false
      return true
    })
  } catch (error) {
    console.error('Error filtering doctors:', error)
    return []
  }
}
