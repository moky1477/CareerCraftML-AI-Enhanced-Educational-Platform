        
       console.log("Javascript Run ho raha hain ") 
        let currentQuestionIndex = 0;
        let questions = [];
        let answers = [];
        let userName = '';
        let jobDescription = '';
        let timerInterval;
        let timePassed = 0;
        const timeLimit = 30; // 30 seconds

        document.getElementById('interview-form').addEventListener('submit', function(e) {
            e.preventDefault();
            startInterview();
        });

        function startInterview() {
            userName = document.getElementById('user_name').value;
            jobDescription = document.getElementById('job_description').value;

            // Store userName and jobDescription in session storage
            sessionStorage.setItem('user_name', userName);
            sessionStorage.setItem('job_description', jobDescription);

            fetch('/start_interview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_name: userName, job_description: jobDescription }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    document.getElementById('interview-form').style.display = 'none';
                    document.getElementById('interview-section').style.display = 'block';
                    questions = data.questions;
                    displayQuestion(currentQuestionIndex);
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        function displayQuestion(index) {
            if (index < questions.length) {
                document.getElementById('question-number').innerText = `Question ${index + 1}`;
                document.getElementById('question-box').innerText = questions[index];
                document.getElementById('timer').innerText = `00:00 / 00:30`;
                document.getElementById('next-question').style.display = 'none';
            }
        }

        document.getElementById('record-answer').addEventListener('click', function() {
            startTimer();
            fetch('/record_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                stopTimer();
                if (data.status === 'success') {
                    answers.push(data.answer);
                    if (currentQuestionIndex < questions.length - 1) {
                        document.getElementById('next-question').style.display = 'block';
                    } else {
                        completeInterview();
                    }
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });

        document.getElementById('next-question').addEventListener('click', function() {
            currentQuestionIndex++;
            displayQuestion(currentQuestionIndex);
        });

        function completeInterview() {
            fetch('/complete_interview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_name: userName,
                    job_description: jobDescription,
                    questions: questions,
                    responses: answers
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    document.getElementById('interview-section').style.display = 'none';
                    document.getElementById('thank-you-section').style.display = 'block';
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        document.getElementById('view-feedback').addEventListener('click', function() {
            // Redirect to the feedback page
            window.location.href = '/feedback';
        });

        document.getElementById('new-interview').addEventListener('click', function() {
            clearSessions();
            resetInterview();
        });

        function clearSessions() {
            fetch('/clear_sessions', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    console.log('Previous interview sessions cleared.');
                } else {
                    console.error('Error: Unable to clear previous interview sessions.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        function resetInterview() {
            currentQuestionIndex = 0;
            questions = [];
            answers = [];
            document.getElementById('user_name').value = '';
            document.getElementById('job_description').value = '';
            document.getElementById('interview-form').style.display = 'block';
            document.getElementById('thank-you-section').style.display = 'none';
        }

        function startTimer() {
            timePassed = 0;
            document.getElementById('record-answer').disabled = true;
            timerInterval = setInterval(() => {
                timePassed++;
                const minutes = String(Math.floor(timePassed / 60)).padStart(2, '0');
                const seconds = String(timePassed % 60).padStart(2, '0');
                document.getElementById('timer').innerText = `${minutes}:${seconds} / 00:30`;
                if (timePassed >= timeLimit) {
                    stopTimer();
                }
            }, 1000);
        }

        function stopTimer() {
            clearInterval(timerInterval);
            document.getElementById('record-answer').disabled = false;
        }
