def suggest_mentors(user_skills, mentors):
    user_skills_list = [s.strip().lower() for s in user_skills.split(",")]
    scored = []

    for mentor in mentors:
        mentor_skills_list = [s.strip().lower() for s in mentor.skills.split(",")]
        score = len(set(user_skills_list) & set(mentor_skills_list))
        if score > 0:
            scored.append((mentor, score))

    # Sort mentors by score (higher match first)
    scored.sort(key=lambda x: x[1], reverse=True)

    # Return mentor data in your dashboard card format
    return [{
        "id": mentor.id,
        "name": mentor.username,
        "skills": mentor.skills,
        "rating": 4.5,  # Placeholder for dynamic rating
        "bio": mentor.bio
    } for mentor, score in scored]
