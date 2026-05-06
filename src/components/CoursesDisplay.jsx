import React, { useState } from 'react';
import APIService from '../APIService.jsx';

const CoursesDisplay = ({ customer }) => {

    const [courses, setCourses] = useState([]);  

    const fetchCourses = () => {
        // Fetch courses for the given customer ID
        APIService.getCoursesForCustomer(customer)
            .then(courses => {
                setCourses(courses);
            })
            .catch(error => {
                console.error('Error fetching courses:', error);
            });
    }

    return (
        <div className="courses-display">
            <h3>Courses for Customer ID: {customer}</h3>
            {courses.length > 0 ? (
                <ul>
                    {courses.map(course => (
                        <li key={course.id}>{course.name}</li>
                    ))}
                </ul>
            ) : (
                <p>No courses found for this customer.</p>
            )}
        </div>
    );
};

export default CoursesDisplay;