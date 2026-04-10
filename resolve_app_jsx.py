import re

def resolve_app_jsx():
    path = r'd:\cryptomentorAI\website-frontend\src\App.jsx'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Resolve RiskManagementCard conflict
    # We want to keep both RiskManagementCard and OnboardingWizard
    content = re.sub(
        r'\n(function RiskManagementCard.*?)\n\n(function OnboardingWizard.*?)\n',
        r'\1\n\n\2',
        content,
        flags=re.DOTALL
    )
    
    # Resolve step handlers conflict
    content = re.sub(
        r'\n(.*?riskSettings\.error.*?)\n\n(.*?Step 2: Risk Config.*?)\n',
        r'\1\n\2',
        content,
        flags=re.DOTALL
    )
    
    # Resolve PortfolioTab conflict
    content = re.sub(
        r'\n(function PortfolioTab.*?)\n\n(function GatekeeperScreen.*?)\n',
        r'\1\n\n\2',
        content,
        flags=re.DOTALL
    )
    
    # Resolve Main Dashboard conflict
    content = re.sub(
        r'\n(function MainDashboard.*?)\n\n(function VerificationPendingScreen.*?)\n',
        r'\1\n\n\2',
        content,
        flags=re.DOTALL
    )
    
    # Clean up any stray markers
    content = content.replace('', '')
    content = content.replace('', '')
    content = content.replace('', '')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Resolved App.jsx")

if __name__ == '__main__':
    resolve_app_jsx()
