document.addEventListener('DOMContentLoaded', () => {
    const sectionLinks = document.querySelectorAll('.section-link');
    const contentSections = document.querySelectorAll('.content-section');

    // Handle section navigation
    sectionLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all links and sections
            sectionLinks.forEach(l => l.classList.remove('active'));
            contentSections.forEach(s => s.classList.remove('active'));
            
            // Add active class to clicked link and corresponding section
            link.classList.add('active');
            const sectionId = link.getAttribute('href').substring(1);
            document.getElementById(sectionId).classList.add('active');
        });
    });

    // Add placeholder cards to each section
    const sections = ['videos', 'papers', 'books', 'github', 'articles'];
    sections.forEach(section => {
        const container = document.querySelector(`#${section} .content-grid`);
        for (let i = 0; i < 4; i++) {
            const card = createPlaceholderCard(section);
            container.appendChild(card);
        }
    });

    function createPlaceholderCard(type) {
        const card = document.createElement('div');
        card.className = 'placeholder-card';
        
        let content = '';
        switch (type) {
            case 'videos':
                content = `
                    <div class="placeholder-image"></div>
                    <div class="placeholder-text">
                        <div class="line"></div>
                        <div class="line"></div>
                    </div>
                `;
                break;
            case 'books':
                content = `
                    <div class="placeholder-image book"></div>
                    <div class="placeholder-text">
                        <div class="line"></div>
                        <div class="line"></div>
                    </div>
                `;
                break;
            default:
                content = `
                    <div class="placeholder-text">
                        <div class="line"></div>
                        <div class="line"></div>
                        <div class="line"></div>
                    </div>
                `;
        }
        
        card.innerHTML = content;
        return card;
    }
});
