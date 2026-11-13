/* Connect the existing Phase 1 pages to the Flask/MySQL backend. */

async function apiRequest(url, options) {
    var response = await fetch(url, options || {});
    var result = await response.json().catch(function () { return {}; });
    if (response.status === 401) {
        window.location.href = "login.html";
        throw new Error("Login required");
    }
    if (!response.ok) {
        throw new Error(result.error || "Request failed");
    }
    return result;
}

async function loadCurrentStudent() {
    var result = await apiRequest("/api/auth/me");
    return result.student;
}

/* Update the signed-in student's name on every page that has a userInfo area. */
async function updateSidebarUser() {
    var student = await loadCurrentStudent();
    var userInfo = document.getElementById("userInfo");
    var welcome = document.getElementById("welcome");

    if (userInfo) {
        userInfo.innerHTML =
            student.first_name + " " + student.last_name +
            " &middot; " + (student.major || "Major not set");
    }

    if (welcome) {
        welcome.innerText = "Welcome back, " + student.first_name;
    }

    return student;
}

function connectLogoutLinks() {
    var links = document.querySelectorAll('.user-info a[href="login.html"]');
    for (var i = 0; i < links.length; i++) {
        links[i].addEventListener("click", async function (event) {
            event.preventDefault();
            await fetch("/api/auth/logout", { method: "POST" });
            window.location.href = "login.html";
        });
    }
}

async function connectMyCourses() {
    var allResult = await apiRequest("/api/courses");
    var mineResult = await apiRequest("/api/my-courses");
    var student = await loadCurrentStudent();

    coursesData.student = student;
    coursesData.allCourses = allResult.courses;
    coursesData.myCourses = mineResult.courses;

    document.getElementById("userInfo").innerHTML =
        student.first_name + " " + student.last_name + " &middot; " + (student.major || "Major not set");

    select.innerHTML = '<option value="">Search and select an SDSU course</option>';
    for (var i = 0; i < coursesData.allCourses.length; i++) {
        var course = coursesData.allCourses[i];
        select.innerHTML += '<option value="' + course.course_id + '">' +
            course.course_code + " " + course.course_name + "</option>";
    }
    showCourses();

    window.addCourse = async function () {
        var error = document.getElementById("error");
        error.innerText = "";
        if (!select.value) {
            error.innerText = "Pick a course first";
            return;
        }
        try {
            await apiRequest("/api/my-courses", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ course_id: Number(select.value) })
            });
            var refreshed = await apiRequest("/api/my-courses");
            coursesData.myCourses = refreshed.courses;
            select.value = "";
            showCourses();
        } catch (errorObject) {
            error.innerText = errorObject.message;
        }
    };

    window.removeCourse = async function (courseId) {
        try {
            await apiRequest("/api/my-courses/" + courseId, { method: "DELETE" });
            var refreshed = await apiRequest("/api/my-courses");
            coursesData.myCourses = refreshed.courses;
            showCourses();
        } catch (errorObject) {
            document.getElementById("error").innerText = errorObject.message;
        }
    };
}

async function connectCreateGroup() {
    var courseResult = await apiRequest("/api/courses");
    var student = await loadCurrentStudent();
    createData.student = student;
    createData.allCourses = courseResult.courses;

    document.getElementById("userInfo").innerHTML =
        student.first_name + " " + student.last_name + " &middot; " + (student.major || "Major not set");

    var courseSelect = document.getElementById("course");
    courseSelect.innerHTML = "";
    for (var i = 0; i < createData.allCourses.length; i++) {
        var course = createData.allCourses[i];
        courseSelect.innerHTML += '<option value="' + course.course_id + '">' +
            course.course_code + " " + course.course_name + "</option>";
    }
    updateName();

    window.createGroup = async function () {
        var course = getCourse(courseSelect.value);
        var start = document.getElementById("startTime").value;
        var end = document.getElementById("endTime").value;
        var location = document.getElementById("location").value.trim();
        var link = document.getElementById("meetingLink").value.trim();

        if (!course || newGroup.days.length === 0) {
            showMessage("Choose a course and at least one meeting day.", "error");
            return;
        }
        if (end <= start) {
            showMessage("End time must be after the start time.", "error");
            return;
        }
        if (newGroup.meeting_format !== "online" && !location) {
            showMessage("Add a meeting location.", "error");
            return;
        }
        if (newGroup.meeting_format === "online" && !link) {
            showMessage("Add the online meeting link.", "error");
            return;
        }

        var meetingLocation = newGroup.meeting_format === "online" ? link : location;
        if (newGroup.meeting_format === "hybrid" && link) {
            meetingLocation = location + " + " + link;
        }
        var meetingTimes = newGroup.days.map(function (day) {
            return { day_of_week: day, start_time: start, end_time: end };
        });

        try {
            var result = await apiRequest("/api/groups", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    course_id: Number(course.course_id),
                    group_name: course.course_code + " Study Group",
                    description: document.getElementById("description").value.trim(),
                    meeting_format: newGroup.meeting_format,
                    meeting_location: meetingLocation,
                    maximum_capacity: Number(document.getElementById("capacity").value),
                    meeting_times: meetingTimes
                })
            });
            showMessage("Group saved successfully.", "success");
            setTimeout(function () {
                window.location.href = "group-details.html?id=" + result.group_id;
            }, 600);
        } catch (errorObject) {
            showMessage(errorObject.message, "error");
        }
    };
}

async function connectFindGroups() {
    var result = await apiRequest("/api/groups" + window.location.search);
    var student = await loadCurrentStudent();
    groupsData.student = student;
    groupsData.groups = result.groups.map(function (group) {
        group.study_style = "Open study group";
        group.approval_required = false;
        return group;
    });
    document.getElementById("userInfo").innerHTML =
        student.first_name + " " + student.last_name + " &middot; " + (student.major || "Major not set");
    showGroups();
    searchGroups();
}

async function connectGroupDetails() {
    var id = new URLSearchParams(window.location.search).get("id");
    if (!id) {
        document.getElementById("message").innerText = "Missing group ID.";
        return;
    }
    var result = await apiRequest("/api/groups/" + id);
    var student = await loadCurrentStudent();
    group = result.group;
    group.tagline = group.description || "Study together and prepare for class.";
    group.study_style = "Open study group";
    group.major_preference = "Any major welcome";
    group.gender_preference = "No gender preference";
    groupData = { student: student, groups: [group] };
    document.getElementById("userInfo").innerHTML =
        student.first_name + " " + student.last_name + " &middot; " + (student.major || "Major not set");
    showGroup();

    window.joinOrLeave = async function () {
        var message = document.getElementById("message");
        try {
            if (isMember()) {
                if (student.student_id === group.leader_id) {
                    message.innerText = "The group leader cannot leave. Delete the group instead.";
                    return;
                }
                await apiRequest("/api/groups/" + group.group_id + "/leave", { method: "DELETE" });
            } else {
                await apiRequest("/api/groups/" + group.group_id + "/join", { method: "POST" });
            }
            var refreshed = await apiRequest("/api/groups/" + group.group_id);
            group = refreshed.group;
            group.tagline = group.description || "Study together and prepare for class.";
            group.study_style = "Open study group";
            group.major_preference = "Any major welcome";
            group.gender_preference = "No gender preference";
            groupData.groups = [group];
            message.innerText = group.is_member ? "You joined the group." : "You left the group.";
            showGroup();
        } catch (errorObject) {
            message.innerText = errorObject.message;
        }
    };
}

async function connectMyGroups() {
    var result = await apiRequest("/api/my-groups");
    var student = await loadCurrentStudent();
    myGroupsData.student = student;
    myGroupsData.groups = result.groups;
    document.getElementById("userInfo").innerHTML =
        student.first_name + " " + student.last_name + " &middot; " + (student.major || "Major not set");
    showNextUp();
    showGroups();
}

async function connectProfile() {
    var student = await loadCurrentStudent();
    var courses = await apiRequest("/api/my-courses");
    var groups = await apiRequest("/api/my-groups");
    profileData.student = student;
    profileData.course_ids = courses.courses.map(function (course) { return course.course_id; });
    profileData.group_ids = groups.groups.map(function (groupItem) { return groupItem.group_id; });
    resetForm();
    showSummary();

    window.saveProfile = async function () {
        var fullName = document.getElementById("fullName").value.trim().split(/\s+/);
        if (fullName.length < 2) {
            showMessage("Enter your first and last name.", "error");
            return;
        }
        try {
            await apiRequest("/api/profile", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    first_name: fullName[0],
                    last_name: fullName.slice(1).join(" "),
                    email: document.getElementById("email").value.trim(),
                    date_of_birth: document.getElementById("dateOfBirth").value,
                    gender: student.gender,
                    major: document.getElementById("major").value,
                    phone_number: document.getElementById("phone").value.trim()
                })
            });
            profileData.student = await loadCurrentStudent();
            resetForm();
            showSummary();
            showMessage("Profile saved to the database.", "success");
        } catch (errorObject) {
            showMessage(errorObject.message, "error");
        }
    };
}

document.addEventListener("DOMContentLoaded", async function () {
    connectLogoutLinks();
    var page = window.location.pathname.split("/").pop();
    try {
        /* This also covers dashboard.html and join-requests.html. */
        await updateSidebarUser();

        if (page === "my-courses.html") await connectMyCourses();
        if (page === "create-group.html") await connectCreateGroup();
        if (page === "find-groups.html") await connectFindGroups();
        if (page === "group-details.html") await connectGroupDetails();
        if (page === "my-groups.html") await connectMyGroups();
        if (page === "profile.html") await connectProfile();
    } catch (errorObject) {
        console.error(errorObject);
    }
});
