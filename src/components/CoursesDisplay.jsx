import React, { useState } from 'react';
import APIService from '../APIService.jsx';

const CoursesDisplay = ({ customer }) => {

    const [courses, setCourses] = useState([]);  

    const fetchCourses = () => {
        // Fetch courses for the given customer ID
        APIService.getCoursesForCustomer(customer.id)
            .then(courses => {
                setCourses(courses);
            })
            .catch(error => {
                console.error('Error fetching courses:', error);
            });
    }

    return (
        <div className="courses-display">
            <h3>Courses for Customer ID: {customer.id}</h3>
            <button onClick={fetchCourses}>Load Courses</button>
            {courses.length > 0 ? (
                <ul>
                    {courses.map(course => (
                        <div key={course.id}>
                            <li>{course.course_name}</li>
                            <li>{course.date_taken}</li>
                        </div>
                    ))}
                </ul>
            ) : (
                <p>No courses found for this customer.</p>
            )}
        </div>
    );
};

export default CoursesDisplay;