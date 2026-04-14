// ===== CONFIGURATION =====
// Google AI Configuration - Easy to upgrade by changing these values
// To upgrade to a newer model:
//   1. Change 'modelName' (e.g., 'gemini-2.0-flash', 'gemini-pro-latest')
//   2. Update 'apiVersion' if needed (e.g., 'v1', 'v2')
//   3. The endpoint will automatically reconstruct
const GOOGLE_AI_CONFIG = {
    apiKey: 'AIzaSyDB4YzUNtAQUqU1_RfJrHGv44TuI4iVS6Y',
    baseUrl: 'https://generativelanguage.googleapis.com',
    apiVersion: 'v1beta',
    modelName: 'gemini-flash-latest', // Updated to working model
    // Construct full endpoint dynamically
    get endpoint() {
        return `${this.baseUrl}/${this.apiVersion}/models/${this.modelName}:generateContent`;
    }
};

// Legacy constants for backward compatibility
const GOOGLE_API_KEY = GOOGLE_AI_CONFIG.apiKey;
const GOOGLE_API_ENDPOINT = GOOGLE_AI_CONFIG.endpoint;

// ===== DATA STORAGE =====
class DataStore {
    constructor() {
        this.skills = this.load('skills') || [];
        this.assessments = this.load('assessments') || {};
        this.evidence = this.load('evidence') || {};
        this.testResults = this.load('testResults') || {};
        this.questionBankData = this.questionBank();
    }

    load(key) {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    }

    save(key, data) {
        localStorage.setItem(key, JSON.stringify(data));
    }

    questionBank() {
        return {
            javascript: [
                // MCQ Questions
                {
                    id: 'js-mcq-1',
                    type: 'mcq',
                    question: 'What is the output of: console.log(typeof null)?',
                    options: ['null', 'undefined', 'object', 'number'],
                    correctAnswer: 2, // index of correct option
                    explanation: 'This is a known JavaScript quirk. typeof null returns "object" due to a legacy bug.',
                    difficulty: 'beginner'
                },
                {
                    id: 'js-mcq-2',
                    type: 'mcq',
                    question: 'Which method can be used to check if an array includes a specific value?',
                    options: ['contains()', 'includes()', 'has()', 'exists()'],
                    correctAnswer: 1,
                    explanation: 'Array.includes() returns true if the array contains the specified value.',
                    difficulty: 'beginner'
                },
                {
                    id: 'js-mcq-3',
                    type: 'mcq',
                    question: 'What is the primary benefit of using async/await over Promises?',
                    options: [
                        'Better performance',
                        'More readable synchronous-looking code',
                        'Automatic error handling',
                        'Faster execution time'
                    ],
                    correctAnswer: 1,
                    explanation: 'Async/await makes asynchronous code look and behave more like synchronous code, improving readability.',
                    difficulty: 'intermediate'
                },
                {
                    id: 'js-mcq-4',
                    type: 'mcq',
                    question: 'Which of the following creates a shallow copy of an array?',
                    options: ['arr.copy()', 'arr.clone()', '[...arr]', 'new Array(arr)'],
                    correctAnswer: 2,
                    explanation: 'The spread operator [...arr] creates a shallow copy of an array.',
                    difficulty: 'intermediate'
                },
                // Scenario Questions
                {
                    id: 'js-1',
                    type: 'scenario',
                    scenario: 'You need to implement a debounce function for a search input that waits 300ms after the user stops typing before making an API call. How would you implement this and why is it important?',
                    difficulty: 'intermediate'
                },
                {
                    id: 'js-2',
                    type: 'scenario',
                    scenario: 'Explain the difference between == and === in JavaScript. Provide examples where using == might cause unexpected behavior.',
                    difficulty: 'beginner'
                },
                {
                    id: 'js-3',
                    type: 'scenario',
                    scenario: 'Design a solution for implementing a custom event emitter class that supports subscribe, unsubscribe, and emit methods. How would you handle memory leaks?',
                    difficulty: 'advanced'
                },
                // Practical Coding Questions
                {
                    id: 'js-code-1',
                    type: 'code',
                    scenario: 'Write a function that removes duplicate values from an array. Explain your approach and discuss time complexity.',
                    difficulty: 'intermediate'
                },
                {
                    id: 'js-code-2',
                    type: 'code',
                    scenario: 'Implement a function that flattens a nested array to any depth. For example: [1, [2, [3, [4]]]] becomes [1, 2, 3, 4]',
                    difficulty: 'intermediate'
                },
                {
                    id: 'js-code-3',
                    type: 'code',
                    scenario: 'Create a memoization function that caches the results of expensive function calls. How would you handle different argument types?',
                    difficulty: 'advanced'
                },
                // Advanced Scenarios
                {
                    id: 'js-perf-1',
                    type: 'scenario',
                    scenario: 'Your web app is experiencing memory leaks. Walk through your debugging approach using Chrome DevTools. What are common causes of memory leaks in JavaScript?',
                    difficulty: 'advanced'
                },
                {
                    id: 'js-arch-1',
                    type: 'scenario',
                    scenario: 'Explain the JavaScript event loop and how it handles synchronous vs asynchronous code. How do microtasks differ from macrotasks?',
                    difficulty: 'advanced'
                }
            ],
            python: [
                // MCQ Questions
                {
                    id: 'py-mcq-1',
                    type: 'mcq',
                    question: 'Which of the following is a mutable data type in Python?',
                    options: ['tuple', 'str', 'list', 'frozenset'],
                    correctAnswer: 2,
                    explanation: 'Lists are mutable - they can be modified after creation.',
                    difficulty: 'beginner'
                },
                {
                    id: 'py-mcq-2',
                    type: 'mcq',
                    question: 'What is the output of: bool([])',
                    options: ['True', 'False', 'None', 'Error'],
                    correctAnswer: 1,
                    explanation: 'Empty containers evaluate to False in Python.',
                    difficulty: 'beginner'
                },
                {
                    id: 'py-mcq-3',
                    type: 'mcq',
                    question: 'Which method is used to add an element to a set?',
                    options: ['append()', 'add()', 'insert()', 'push()'],
                    correctAnswer: 1,
                    explanation: 'set.add() adds a single element to a set.',
                    difficulty: 'beginner'
                },
                // Scenario Questions
                {
                    id: 'py-1',
                    type: 'scenario',
                    scenario: 'You have a list of 1 million dictionaries and need to find all duplicates based on a specific key. What approach would you use and why?',
                    difficulty: 'intermediate'
                },
                {
                    id: 'py-2',
                    type: 'scenario',
                    scenario: 'Explain the difference between a list and a tuple in Python. When would you use one over the other?',
                    difficulty: 'beginner'
                },
                {
                    id: 'py-3',
                    type: 'scenario',
                    scenario: 'Implement a decorator that caches function results and automatically invalidates the cache after 5 minutes. How would you handle thread safety?',
                    difficulty: 'advanced'
                },
                // Code Questions
                {
                    id: 'py-code-1',
                    type: 'code',
                    scenario: 'Write a generator function that yields the Fibonacci sequence. What are the memory benefits of using generators?',
                    difficulty: 'intermediate'
                },
                {
                    id: 'py-code-2',
                    type: 'code',
                    scenario: 'Implement a context manager for database connections that ensures proper cleanup even if exceptions occur.',
                    difficulty: 'advanced'
                },
                {
                    id: 'py-adv-1',
                    type: 'scenario',
                    scenario: 'Explain the Global Interpreter Lock (GIL) and its impact on multi-threaded Python applications. When would you use multiprocessing instead?',
                    difficulty: 'advanced'
                },
                {
                    id: 'py-adv-2',
                    type: 'scenario',
                    scenario: 'How do you optimize a Python application for performance? Discuss profiling tools and common optimization strategies.',
                    difficulty: 'advanced'
                }
            ],
            react: [
                // MCQ Questions
                {
                    id: 'react-mcq-1',
                    type: 'mcq',
                    question: 'Which hook is used for side effects in React?',
                    options: ['useState', 'useEffect', 'useContext', 'useMemo'],
                    correctAnswer: 1,
                    explanation: 'useEffect manages side effects like data fetching and subscriptions.',
                    difficulty: 'beginner'
                },
                {
                    id: 'react-mcq-2',
                    type: 'mcq',
                    question: 'What does React.memo do?',
                    options: [
                        'Prevents component from re-rendering if props haven\'t changed',
                        'Memorizes state values',
                        'Caches API responses',
                        'Optimizes CSS rendering'
                    ],
                    correctAnswer: 0,
                    explanation: 'React.memo is a higher-order component that memoizes the result, preventing unnecessary re-renders.',
                    difficulty: 'intermediate'
                },
                {
                    id: 'react-mcq-3',
                    type: 'mcq',
                    question: 'When should you use useCallback?',
                    options: [
                        'To cache expensive calculations',
                        'To prevent function recreation on re-renders',
                        'To fetch data from APIs',
                        'To manage global state'
                    ],
                    correctAnswer: 1,
                    explanation: 'useCallback memoizes functions to prevent recreation on re-renders, useful for optimization.',
                    difficulty: 'intermediate'
                },
                // Scenario Questions
                {
                    id: 'react-1',
                    type: 'scenario',
                    scenario: 'Your React application is re-rendering too frequently causing performance issues. Walk through your debugging process and optimization strategies.',
                    difficulty: 'intermediate'
                },
                {
                    id: 'react-2',
                    type: 'scenario',
                    scenario: 'Explain what props are in React and how they differ from state. Provide an example of when to use each.',
                    difficulty: 'beginner'
                },
                {
                    id: 'react-3',
                    type: 'scenario',
                    scenario: 'Design a custom hook for managing complex form state with validation, error handling, and submit logic. How would you make it reusable across different forms?',
                    difficulty: 'advanced'
                },
                // Code Questions
                {
                    id: 'react-code-1',
                    type: 'code',
                    scenario: 'Build a custom hook called useDebounce that debounces a value. How would you implement cleanup to prevent memory leaks?',
                    difficulty: 'intermediate'
                },
                {
                    id: 'react-code-2',
                    type: 'code',
                    scenario: 'Create a higher-order component (HOC) that adds loading and error handling to any component that fetches data.',
                    difficulty: 'advanced'
                },
                {
                    id: 'react-arch-1',
                    type: 'scenario',
                    scenario: 'Explain the Virtual DOM and how React uses it for efficient updates. What are the performance implications?',
                    difficulty: 'advanced'
                }
            ],
            'project management': [
                {
                    id: 'pm-1',
                    scenario: 'Your project is behind schedule and the client is pressuring for delivery. How would you assess the situation and communicate with stakeholders?',
                    difficulty: 'intermediate'
                },
                {
                    id: 'pm-2',
                    scenario: 'What are the key differences between Agile and Waterfall project management methodologies? When would you choose one over the other?',
                    difficulty: 'beginner'
                },
                {
                    id: 'pm-3',
                    scenario: 'You are managing a cross-functional team with conflicting priorities and limited resources. How would you optimize resource allocation and maintain team morale?',
                    difficulty: 'advanced'
                }
            ],
            communication: [
                {
                    id: 'comm-1',
                    scenario: 'You need to present a technical concept to non-technical stakeholders. How would you structure your presentation and what strategies would you use?',
                    difficulty: 'intermediate'
                },
                {
                    id: 'comm-2',
                    scenario: 'Describe a time when you had to give constructive feedback to a colleague. What approach did you take?',
                    difficulty: 'beginner'
                },
                {
                    id: 'comm-3',
                    scenario: 'You are mediating a conflict between two senior team members with different architectural visions. How would you facilitate resolution while maintaining technical excellence?',
                    difficulty: 'advanced'
                }
            ]
        };
    }
}

const dataStore = new DataStore();

// ===== NAVIGATION =====
function navigateTo(pageName) {
    // Update navigation buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.page === pageName) {
            btn.classList.add('active');
        }
    });

    // Update pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(`${pageName}-page`).classList.add('active');

    // Load page-specific data
    switch (pageName) {
        case 'skills':
            loadSkills();
            break;
        case 'assess':
            loadAssessmentSkills();
            break;
        case 'test':
            loadTestSkills();
            break;
        case 'results':
            loadResults();
            break;
        case 'resume':
            generateResume();
            break;
    }
}

// Set up navigation event listeners
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            navigateTo(btn.dataset.page);
        });
    });

    // Setup slider listeners
    setupSliderListeners();

    // Load initial skills
    loadSkills();
});

// ===== SKILLS MANAGEMENT =====
function loadSkills() {
    const categories = {
        technical: document.getElementById('technical-skills'),
        analytical: document.getElementById('analytical-skills'),
        soft: document.getElementById('soft-skills')
    };

    // Clear existing
    Object.values(categories).forEach(el => el.innerHTML = '');

    // Populate skills
    dataStore.skills.forEach(skill => {
        const skillCard = createSkillCard(skill);
        if (categories[skill.category]) {
            categories[skill.category].appendChild(skillCard);
        }
    });

    // Show placeholder if empty
    Object.keys(categories).forEach(category => {
        if (categories[category].children.length === 0) {
            categories[category].innerHTML = '<p style="color: var(--text-muted); font-style: italic;">No skills added yet</p>';
        }
    });
}

function createSkillCard(skill) {
    const card = document.createElement('div');
    card.className = 'skill-card';
    card.innerHTML = `
        <span class="skill-card-name">${skill.name}</span>
        <div class="skill-card-actions">
            <button class="icon-btn delete-skill-btn" data-skill-id="${skill.id}" title="Delete">🗑️</button>
        </div>
    `;

    // Add event listener for delete button
    const deleteBtn = card.querySelector('.delete-skill-btn');
    deleteBtn.addEventListener('click', function () {
        deleteSkill(skill.id);
    });

    return card;
}

function openAddSkillModal() {
    document.getElementById('add-skill-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('add-skill-modal').classList.remove('active');
    document.getElementById('new-skill-name').value = '';
}

function addSkill() {
    const name = document.getElementById('new-skill-name').value.trim();
    const category = document.getElementById('new-skill-category').value;

    if (!name) {
        alert('Please enter a skill name');
        return;
    }

    const skill = {
        id: generateId(),
        name: name,
        category: category
    };

    dataStore.skills.push(skill);
    dataStore.save('skills', dataStore.skills);

    closeModal();
    loadSkills();

    // Show success message
    showNotification('Skill added successfully!');
}

function deleteSkill(skillId) {
    if (!confirm('Are you sure you want to delete this skill?')) {
        return;
    }

    dataStore.skills = dataStore.skills.filter(s => s.id !== skillId);
    dataStore.save('skills', dataStore.skills);

    // Clean up related data
    delete dataStore.assessments[skillId];
    delete dataStore.evidence[skillId];
    delete dataStore.testResults[skillId];
    dataStore.save('assessments', dataStore.assessments);
    dataStore.save('evidence', dataStore.evidence);
    dataStore.save('testResults', dataStore.testResults);

    // Refresh all pages that show skills
    loadSkills();

    // Also refresh assessment and test dropdowns if they exist
    const assessSelect = document.getElementById('assess-skill-select');
    if (assessSelect) {
        loadAssessmentSkills();
    }

    const testSelect = document.getElementById('test-skill-select');
    if (testSelect) {
        loadTestSkills();
    }

    showNotification('Skill deleted');
}

// ===== ASSESSMENT =====
function loadAssessmentSkills() {
    const select = document.getElementById('assess-skill-select');
    select.innerHTML = '<option value="">-- Choose a skill --</option>';

    dataStore.skills.forEach(skill => {
        const option = document.createElement('option');
        option.value = skill.id;
        option.textContent = skill.name;
        select.appendChild(option);
    });
}

function loadAssessmentForm() {
    const skillId = document.getElementById('assess-skill-select').value;
    const form = document.getElementById('assessment-form');

    if (!skillId) {
        form.style.display = 'none';
        return;
    }

    form.style.display = 'block';

    // Load existing assessment if available
    const existing = dataStore.assessments[skillId];
    if (existing) {
        document.getElementById('knowledge-slider').value = existing.knowledge;
        document.getElementById('application-slider').value = existing.application;
        document.getElementById('independence-slider').value = existing.independence;
        document.getElementById('complexity-slider').value = existing.complexityHandling;

        updateSliderValues();
    }

    // Load existing evidence
    const existingEvidence = dataStore.evidence[skillId];
    if (existingEvidence) {
        document.getElementById('tools-input').value = existingEvidence.tools.join(', ');
        document.getElementById('tasks-input').value = existingEvidence.tasks.join(', ');
        document.getElementById('projects-input').value = existingEvidence.projects.join(', ');
    }
}

function setupSliderListeners() {
    const sliders = ['knowledge', 'application', 'independence', 'complexity'];
    sliders.forEach(name => {
        const slider = document.getElementById(`${name}-slider`);
        if (slider) {
            slider.addEventListener('input', updateSliderValues);
        }
    });
}

function updateSliderValues() {
    const sliders = ['knowledge', 'application', 'independence', 'complexity'];
    sliders.forEach(name => {
        const slider = document.getElementById(`${name}-slider`);
        const valueDisplay = document.getElementById(`${name}-value`);
        if (slider && valueDisplay) {
            valueDisplay.textContent = slider.value;
        }
    });
}

function submitAssessment() {
    const skillId = document.getElementById('assess-skill-select').value;
    if (!skillId) {
        alert('Please select a skill');
        return;
    }

    const assessment = {
        knowledge: parseInt(document.getElementById('knowledge-slider').value),
        application: parseInt(document.getElementById('application-slider').value),
        independence: parseInt(document.getElementById('independence-slider').value),
        complexityHandling: parseInt(document.getElementById('complexity-slider').value)
    };

    const evidence = {
        tools: document.getElementById('tools-input').value.split(',').map(s => s.trim()).filter(s => s),
        tasks: document.getElementById('tasks-input').value.split(',').map(s => s.trim()).filter(s => s),
        projects: document.getElementById('projects-input').value.split(',').map(s => s.trim()).filter(s => s)
    };

    dataStore.assessments[skillId] = assessment;
    dataStore.evidence[skillId] = evidence;
    dataStore.save('assessments', dataStore.assessments);
    dataStore.save('evidence', dataStore.evidence);

    showNotification('Assessment saved successfully!');
}

// ===== TESTING =====
let currentTest = {
    skillId: null,
    skillName: null,
    questions: [],
    currentQuestionIndex: 0,
    answers: []
};

function loadTestSkills() {
    const select = document.getElementById('test-skill-select');
    select.innerHTML = '<option value="">-- Choose a skill --</option>';

    dataStore.skills.forEach(skill => {
        const option = document.createElement('option');
        option.value = skill.id;
        option.textContent = skill.name;
        select.appendChild(option);
    });
}

function loadTest() {
    const skillId = document.getElementById('test-skill-select').value;
    if (!skillId) {
        document.getElementById('test-content').style.display = 'none';
        return;
    }

    const skill = dataStore.skills.find(s => s.id === skillId);
    const skillNameLower = skill.name.toLowerCase();

    // Get questions from question bank
    let questions = dataStore.questionBankData[skillNameLower] || [];

    if (questions.length === 0) {
        // Generate generic questions if skill not in bank
        questions = generateGenericQuestions(skill.name);
    }

    currentTest = {
        skillId: skillId,
        skillName: skill.name,
        questions: questions,
        currentQuestionIndex: 0,
        answers: new Array(questions.length).fill(null)
    };

    document.getElementById('test-content').style.display = 'block';
    document.getElementById('feedback-section').style.display = 'none';
    displayCurrentQuestion();
}

function generateGenericQuestions(skillName) {
    return [
        {
            id: `${skillName}-1`,
            scenario: `Describe your experience with ${skillName}. What are the key concepts you understand?`,
            difficulty: 'beginner'
        },
        {
            id: `${skillName}-2`,
            scenario: `Explain a challenging problem you solved using ${skillName}. What was your approach?`,
            difficulty: 'intermediate'
        },
        {
            id: `${skillName}-3`,
            scenario: `How would you teach ${skillName} to someone new? What best practices would you emphasize?`,
            difficulty: 'advanced'
        }
    ];
}

function displayCurrentQuestion() {
    const question = currentTest.questions[currentTest.currentQuestionIndex];

    document.getElementById('question-number').textContent =
        `Question ${currentTest.currentQuestionIndex + 1} of ${currentTest.questions.length}`;

    // Show question type badge
    const questionType = question.type || 'scenario';
    const typeText = questionType === 'mcq' ? 'Multiple Choice' : questionType === 'code' ? 'Code Challenge' : 'Scenario';

    // Update difficulty badge
    const difficultyBadge = document.getElementById('difficulty-badge');
    difficultyBadge.textContent = question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1);
    difficultyBadge.className = `difficulty-badge ${question.difficulty}`;

    // Add type indicator next to difficulty
    difficultyBadge.textContent += ` ΓÇó ${typeText}`;

    // Handle MCQ vs Text questions
    const questionScenario = document.getElementById('question-scenario');
    const answerInput = document.getElementById('answer-input');

    if (question.type === 'mcq') {
        // Display MCQ
        questionScenario.innerHTML = `
            <div style="margin-bottom: 1rem; font-weight: 500;">${question.question}</div>
            <div class="mcq-options">
                ${question.options.map((opt, idx) => `
                    <label class="mcq-option">
                        <input type="radio" name="mcq-answer" value="${idx}" 
                            ${currentTest.answers[currentTest.currentQuestionIndex]?.answer == idx ? 'checked' : ''}>
                        <span>${opt}</span>
                    </label>
                `).join('')}
            </div>
        `;
        answerInput.style.display = 'none';
    } else {
        // Display scenario/code question
        questionScenario.textContent = question.scenario;
        answerInput.style.display = 'block';

        // Load saved answer if exists
        const savedAnswer = currentTest.answers[currentTest.currentQuestionIndex];
        answerInput.value = savedAnswer ? savedAnswer.answer : '';
    }
}

function previousQuestion() {
    if (currentTest.currentQuestionIndex > 0) {
        currentTest.currentQuestionIndex--;
        displayCurrentQuestion();
        document.getElementById('feedback-section').style.display = 'none';
    }
}

function nextQuestion() {
    if (currentTest.currentQuestionIndex < currentTest.questions.length - 1) {
        currentTest.currentQuestionIndex++;
        displayCurrentQuestion();
        document.getElementById('feedback-section').style.display = 'none';
    } else {
        showNotification('Test completed! View your results in the Results page.');
        navigateTo('results');
    }
}

async function submitAnswer() {
    const question = currentTest.questions[currentTest.currentQuestionIndex];
    let answer;
    let score;
    let feedback;

    // Get answer based on question type
    if (question.type === 'mcq') {
        const selected = document.querySelector('input[name="mcq-answer"]:checked');
        if (!selected) {
            alert('Please select an answer');
            return;
        }
        answer = parseInt(selected.value);

        // Auto-score MCQ
        const isCorrect = answer === question.correctAnswer;
        score = isCorrect ? 100 : 0;
        feedback = isCorrect
            ? `Correct! ${question.explanation || ''}`
            : `Incorrect. The correct answer is "${question.options[question.correctAnswer]}". ${question.explanation || ''}`;

        // Save answer immediately for MCQ
        currentTest.answers[currentTest.currentQuestionIndex] = {
            answer: answer,
            score: score,
            feedback: feedback
        };

        // Update test results in storage
        if (!dataStore.testResults[currentTest.skillId]) {
            dataStore.testResults[currentTest.skillId] = [];
        }
        dataStore.testResults[currentTest.skillId][currentTest.currentQuestionIndex] = {
            questionId: question.id,
            userAnswer: answer,
            score: score,
            feedback: feedback,
            timestamp: new Date().toISOString()
        };
        dataStore.save('testResults', dataStore.testResults);

        // Display feedback immediately
        document.getElementById('score-value').textContent = score;
        document.getElementById('feedback-text').textContent = feedback;
        document.getElementById('feedback-section').style.display = 'block';

    } else {
        // Text answer - use AI evaluation
        answer = document.getElementById('answer-input').value.trim();

        if (!answer) {
            alert('Please provide an answer');
            return;
        }

        // Show loading state
        const submitBtn = event?.target || document.querySelector('.btn-primary[onclick="submitAnswer()"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> Evaluating with AI...';
        }

        try {
            // Call Google AI API for evaluation
            const evaluation = await evaluateAnswerWithAI(question, answer);

            // Save answer and evaluation
            currentTest.answers[currentTest.currentQuestionIndex] = {
                answer: answer,
                score: evaluation.score,
                feedback: evaluation.feedback
            };

            // Update test results in storage
            if (!dataStore.testResults[currentTest.skillId]) {
                dataStore.testResults[currentTest.skillId] = [];
            }
            dataStore.testResults[currentTest.skillId][currentTest.currentQuestionIndex] = {
                questionId: question.id,
                userAnswer: answer,
                score: evaluation.score,
                feedback: evaluation.feedback,
                timestamp: new Date().toISOString()
            };
            dataStore.save('testResults', dataStore.testResults);

            // Display feedback
            document.getElementById('score-value').textContent = evaluation.score;
            document.getElementById('feedback-text').textContent = evaluation.feedback;
            document.getElementById('feedback-section').style.display = 'block';

        } catch (error) {
            console.error('Evaluation error:', error);
            alert(error.message || 'Failed to evaluate answer. Please check your internet connection and try again.');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Answer';
            }
        }
    }
}

async function evaluateAnswerWithAI(question, userAnswer) {
    const prompt = `You are an expert evaluator assessing a candidate's answer to a skill-based question.

Question Difficulty: ${question.difficulty}
Question: ${question.scenario}

Candidate's Answer: ${userAnswer}

Please evaluate this answer and provide:
1. A score from 0-100 based on:
   - Correctness and accuracy (40%)
   - Depth of understanding (30%)
   - Practical application (20%)
   - Communication clarity (10%)

2. Constructive feedback (2-3 sentences) highlighting strengths and areas for improvement.

Respond in this exact JSON format:
{
  "score": <number 0-100>,
  "feedback": "<your feedback here>"
}`;

    try {
        const response = await fetch(`${GOOGLE_API_ENDPOINT}?key=${GOOGLE_API_KEY}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                contents: [{
                    parts: [{
                        text: prompt
                    }]
                }]
            })
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();
        const aiResponse = data.candidates[0].content.parts[0].text;

        // Extract JSON from response (handle markdown code blocks)
        let jsonText = aiResponse;
        if (aiResponse.includes('```json')) {
            jsonText = aiResponse.split('```json')[1].split('```')[0].trim();
        } else if (aiResponse.includes('```')) {
            jsonText = aiResponse.split('```')[1].split('```')[0].trim();
        }

        const evaluation = JSON.parse(jsonText);

        return {
            score: Math.min(100, Math.max(0, evaluation.score)),
            feedback: evaluation.feedback
        };

    } catch (error) {
        console.error('AI evaluation error:', error);
        // Show real error instead of fake scoring
        throw new Error(`AI Evaluation Failed: ${error.message}. Please check your internet connection and try again.`);
    }
}

// ===== RESULTS =====
function loadResults() {
    const container = document.getElementById('results-container');
    container.innerHTML = '';

    if (dataStore.skills.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No skills added yet. Add skills to get started!</p>';
        return;
    }

    dataStore.skills.forEach(skill => {
        const resultCard = createResultCard(skill);
        container.appendChild(resultCard);
    });
}

function createResultCard(skill) {
    const assessment = dataStore.assessments[skill.id];
    const testResults = dataStore.testResults[skill.id] || [];
    const evidence = dataStore.evidence[skill.id];

    // Calculate scores
    let selfScore = 0;
    let testScore = 0;
    let finalLevel = 0;

    if (assessment) {
        selfScore = (assessment.knowledge + assessment.application +
            assessment.independence + assessment.complexityHandling) / 4;
    }

    if (testResults.length > 0) {
        const avgTestScore = testResults.reduce((sum, r) => sum + (r.score || 0), 0) / testResults.length;
        testScore = (avgTestScore / 100) * 5; // Convert to 1-5 scale
    }

    // Hybrid score (60% self, 40% test)
    if (selfScore > 0 && testScore > 0) {
        finalLevel = (selfScore * 0.6 + testScore * 0.4).toFixed(1);
    } else if (selfScore > 0) {
        finalLevel = selfScore.toFixed(1);
    } else if (testScore > 0) {
        finalLevel = testScore.toFixed(1);
    }

    const card = document.createElement('div');
    card.className = 'result-card';

    let evidenceHtml = '';
    if (evidence) {
        const allEvidence = [...evidence.tools, ...evidence.tasks, ...evidence.projects].filter(e => e);
        if (allEvidence.length > 0) {
            evidenceHtml = `
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
                    <strong style="color: var(--text-secondary);">Evidence:</strong>
                    <p style="color: var(--text-muted); margin-top: 0.5rem;">${allEvidence.join(', ')}</p>
                </div>
            `;
        }
    }

    let testFeedbackHtml = '';
    if (testResults.length > 0) {
        testFeedbackHtml = `
            <div style="margin-top: 1rem;">
                <strong style="color: var(--text-secondary);">Recent AI Feedback:</strong>
                ${testResults.slice(-2).map(r => `
                    <p style="color: var(--text-muted); margin-top: 0.5rem; font-size: 0.9rem;">
                        Score: ${r.score}/100 - ${r.feedback}
                    </p>
                `).join('')}
            </div>
        `;
    }

    card.innerHTML = `
        <div class="result-header">
            <span class="result-skill-name">${skill.name}</span>
            <span class="result-level">${finalLevel > 0 ? finalLevel + '/5' : 'Not assessed'}</span>
        </div>
        ${finalLevel > 0 ? `
            <div class="result-breakdown">
                <div class="breakdown-item">
                    <div class="breakdown-label">Self-Assessment</div>
                    <div class="breakdown-value">${selfScore.toFixed(1)}/5</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-label">Test Performance</div>
                    <div class="breakdown-value">${testScore > 0 ? testScore.toFixed(1) + '/5' : 'Not tested'}</div>
                </div>
            </div>
        ` : '<p style="color: var(--text-muted); margin-top: 1rem;">Complete assessment and tests to see results</p>'}
        ${evidenceHtml}
        ${testFeedbackHtml}
    `;

    return card;
}

// ===== RESUME GENERATION =====
function generateResume() {
    const content = document.getElementById('resume-content');
    content.innerHTML = '';

    if (dataStore.skills.length === 0) {
        content.innerHTML = '<p style="text-align: center; color: #999;">No skills to display. Add and assess skills first.</p>';
        return;
    }

    dataStore.skills.forEach(skill => {
        const assessment = dataStore.assessments[skill.id];
        const testResults = dataStore.testResults[skill.id] || [];
        const evidence = dataStore.evidence[skill.id];

        // Calculate level
        let level = 0;
        let selfScore = 0;
        let testScore = 0;

        if (assessment) {
            selfScore = (assessment.knowledge + assessment.application +
                assessment.independence + assessment.complexityHandling) / 4;
        }

        if (testResults.length > 0) {
            const avgTestScore = testResults.reduce((sum, r) => sum + (r.score || 0), 0) / testResults.length;
            testScore = (avgTestScore / 100) * 5;
        }

        if (selfScore > 0 && testScore > 0) {
            level = (selfScore * 0.6 + testScore * 0.4);
        } else if (selfScore > 0) {
            level = selfScore;
        } else if (testScore > 0) {
            level = testScore;
        }

        if (level === 0) return; // Skip unevaluated skills

        // Map level to proficiency
        let proficiency = '';
        if (level >= 4.5) proficiency = 'Expert';
        else if (level >= 3.5) proficiency = 'Advanced';
        else if (level >= 2.5) proficiency = 'Intermediate';
        else if (level >= 1.5) proficiency = 'Proficient';
        else proficiency = 'Beginner';

        // Get evidence
        let evidenceStr = '';
        if (evidence) {
            const allEvidence = [...evidence.tools, ...evidence.tasks, ...evidence.projects].filter(e => e);
            if (allEvidence.length > 0) {
                evidenceStr = allEvidence.slice(0, 3).join(', ');
            }
        }

        const line = document.createElement('div');
        line.className = 'resume-skill-line';
        line.innerHTML = `
            <span class="resume-skill-name">${skill.name}</span> — 
            <span class="resume-skill-level">${proficiency}</span>
            ${evidenceStr ? ` <span class="resume-skill-evidence">(${evidenceStr})</span>` : ''}
        `;
        content.appendChild(line);
    });
}

function copyResumeText() {
    const content = document.getElementById('resume-content');
    const text = content.innerText;

    navigator.clipboard.writeText('SKILLS\n\n' + text).then(() => {
        showNotification('Resume text copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    });
}

// ===== UTILITY FUNCTIONS =====
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function showNotification(message) {
    // Simple notification (could be enhanced with a toast library)
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--primary-gradient);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-lg);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
