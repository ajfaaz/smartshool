def get_teacher_assignments(teacher):
    return teacher.teachersubject_set.select_related("subject", "student_class").order_by(
        "student_class__name", "subject__name"
    )


def get_teacher_class_names(teacher):
    return list(
        get_teacher_assignments(teacher).values_list("student_class__name", flat=True).distinct()
    )


def get_teacher_subject_ids(teacher):
    return list(
        get_teacher_assignments(teacher).values_list("subject_id", flat=True).distinct()
    )
