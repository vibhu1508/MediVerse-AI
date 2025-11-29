'use client'

import React, { useState } from 'react'
import { searchDoctors, type Doctor } from '@/services/recommendationService'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export default function RecommendationsPage() {
  const [city, setCity] = useState('')
  const [specialization, setSpecialization] = useState('')
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSearch() {
    if (!city.trim() || !specialization.trim()) {
      setError('Please enter both city and specialization')
      return
    }

    try {
      setLoading(true)
      setError('')
      const results = await searchDoctors(city, specialization, 3)
      setDoctors(results)
    } catch (err) {
      setError('Failed to search doctors. Please try again.')
      console.error('Search error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen p-8 bg-slate-50">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Find Doctors</h1>
          <p className="text-slate-600 mt-2">Search for healthcare professionals by location and specialization</p>
        </div>

        {/* Search Form */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8 border border-slate-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                City
              </label>
              <Input
                type="text"
                placeholder="e.g., Mumbai, Delhi, Bangalore"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Specialization
              </label>
              <Input
                type="text"
                placeholder="e.g., Cardiologist, Neurologist"
                value={specialization}
                onChange={(e) => setSpecialization(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={handleSearch}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              >
                {loading ? 'Searching...' : 'Search'}
              </Button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
            {error}
          </div>
        )}

        {/* Results */}
        {doctors.length > 0 && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600">Found {doctors.length} doctors</p>
            {doctors.map((doctor, index) => (
              <div
                key={doctor.id}
                className={`bg-white rounded-lg p-6 border ${
                  index === 0 ? 'border-green-200 border-2' : 'border-slate-200'
                } shadow-sm hover:shadow-md transition-shadow`}
              >
                <div className="flex items-start justify-between gap-4">
                  {doctor.image && (
                    <img
                      src={doctor.image}
                      alt={doctor.name}
                      className="w-16 h-16 rounded-full object-cover"
                      onError={(e) => {
                        const img = e.target as HTMLImageElement
                        img.src = 'https://via.placeholder.com/64'
                      }}
                    />
                  )}
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-semibold text-slate-900 truncate">
                        {doctor.name}
                        {index === 0 && <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Top Match</span>}
                      </h3>
                    </div>
                    
                    <p className="text-sm text-slate-600 mb-2">{doctor.specialization}</p>
                    <p className="text-sm text-slate-600 mb-3">{doctor.hospital}</p>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                      <div>
                        <span className="text-slate-500">Rating</span>
                        <p className="font-semibold text-slate-900">{doctor.rating}%</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Reviews</span>
                        <p className="font-semibold text-slate-900">{doctor.reviews}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Experience</span>
                        <p className="font-semibold text-slate-900">{doctor.experience} yrs</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Fees</span>
                        <p className="font-semibold text-slate-900">₹{doctor.fees}</p>
                      </div>
                    </div>
                  </div>

                  {doctor.profile_link && doctor.profile_link !== '#' && (
                    <a
                      href={doctor.profile_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm whitespace-nowrap"
                    >
                      View Profile
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && doctors.length === 0 && city && specialization && (
          <div className="text-center py-12">
            <p className="text-slate-600">No doctors found. Try different search criteria.</p>
          </div>
        )}

        {!loading && doctors.length === 0 && (!city || !specialization) && (
          <div className="text-center py-12">
            <p className="text-slate-600">Enter city and specialization to search for doctors</p>
          </div>
        )}
      </div>
    </main>
  )
}
