document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('newProjectModal');
    const newProjectBtn = document.getElementById('newProjectBtn');
    const closeBtn = document.querySelector('.close-btn');
    const cancelBtn = document.getElementById('cancelBtn');
    const newProjectForm = document.getElementById('newProjectForm');

    // Open modal
    newProjectBtn.addEventListener('click', () => {
        modal.classList.add('active');
    });

    // Close modal functions
    const closeModal = () => {
        modal.classList.remove('active');
        newProjectForm.reset();
    };

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    // Handle form submission
    newProjectForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const title = document.getElementById('projectTitle').value;
        const prompt = document.getElementById('projectPrompt').value;

        try {
            const response = await fetch('/api/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title, prompt }),
            });

            if (response.ok) {
                const project = await response.json();
                window.location.href = `/project/${project.id}`;
            } else {
                console.error('Failed to create project');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });
});
