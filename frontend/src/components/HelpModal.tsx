import { useState } from 'react';
import { X, BookOpen, Key, Sparkles, Filter, Search, Bookmark, ChevronRight } from 'lucide-react';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type SectionType = 'guide' | 'api' | 'ai' | 'preset' | 'search' | 'shortcuts';

export default function HelpModal({ isOpen, onClose }: HelpModalProps) {
  const [activeSection, setActiveSection] = useState<SectionType>('guide');

  if (!isOpen) return null;

  const sections = [
    { id: 'guide' as SectionType, label: '기본 사용법', icon: BookOpen },
    { id: 'api' as SectionType, label: 'API 설정 가이드', icon: Key },
    { id: 'ai' as SectionType, label: 'AI 필터링', icon: Sparkles },
    { id: 'preset' as SectionType, label: '프리셋 활용', icon: Filter },
    { id: 'search' as SectionType, label: '뉴스 검색', icon: Search },
    { id: 'shortcuts' as SectionType, label: '단축키', icon: Bookmark },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[85vh] overflow-hidden flex">
        {/* Sidebar */}
        <div className="w-52 bg-gray-50 border-r p-4">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            도움말
          </h2>
          <nav className="space-y-1">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  activeSection === section.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <section.icon className="w-4 h-4" />
                {section.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h3 className="font-semibold">
              {sections.find((s) => s.id === activeSection)?.label}
            </h3>
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeSection === 'guide' && <GuideSection />}
            {activeSection === 'api' && <APIGuideSection />}
            {activeSection === 'ai' && <AIGuideSection />}
            {activeSection === 'preset' && <PresetGuideSection />}
            {activeSection === 'search' && <SearchGuideSection />}
            {activeSection === 'shortcuts' && <ShortcutsSection />}
          </div>
        </div>
      </div>
    </div>
  );
}

function GuideSection() {
  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-lg font-semibold mb-3">Korean News Filter란?</h4>
        <p className="text-gray-600 leading-relaxed">
          Korean News Filter는 유튜브 콘텐츠 기획을 위한 한국 뉴스 수집 및 AI 필터링 도구입니다.
          브랜드 스토리(실패, 성공, 부활), 프랜차이즈, 스타트업 관련 뉴스를 수집하고,
          AI를 통해 유튜브 콘텐츠로 적합한 기사를 자동으로 선별해줍니다.
        </p>
      </div>

      <div>
        <h4 className="text-lg font-semibold mb-3">주요 기능</h4>
        <div className="space-y-3">
          <FeatureItem
            title="🔍 네이버 검색 (Search)"
            description="네이버 뉴스 검색 API로 키워드 기반 뉴스를 검색하여 수집합니다."
          />
          <FeatureItem
            title="✨ AI 분석 (AI Filter)"
            description="Gemini AI가 뉴스의 유튜브 콘텐츠 적합도를 분석합니다."
          />
          <FeatureItem
            title="📋 프리셋 필터"
            description="미리 설정된 키워드 조합으로 빠르게 필터링합니다."
          />
          <FeatureItem
            title="⭐ 북마크"
            description="관심 있는 기사를 북마크하여 나중에 확인합니다."
          />
        </div>
      </div>

      <div>
        <h4 className="text-lg font-semibold mb-3">시작하기</h4>
        <ol className="space-y-2 text-gray-600">
          <li className="flex gap-2">
            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">1</span>
            <span><strong>Search</strong> 버튼을 눌러 키워드로 뉴스를 검색하세요.</span>
          </li>
          <li className="flex gap-2">
            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">2</span>
            <span>좌측 <strong>프리셋</strong>을 클릭하여 원하는 주제의 뉴스를 필터링하세요.</span>
          </li>
          <li className="flex gap-2">
            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">3</span>
            <span>뉴스 카드의 <strong>✨ 아이콘</strong>을 눌러 AI 분석을 실행하세요.</span>
          </li>
          <li className="flex gap-2">
            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">4</span>
            <span>관심 있는 기사는 <strong>⭐ 북마크</strong>해두세요.</span>
          </li>
        </ol>
      </div>
    </div>
  );
}

function APIGuideSection() {
  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-lg font-semibold mb-3">Gemini API 설정</h4>
        <p className="text-gray-600 mb-4">
          AI 분석 기능을 사용하려면 Google Gemini API 키가 필요합니다.
        </p>

        <div className="space-y-4">
          <Step number={1} title="Google AI Studio 접속">
            <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer"
               className="text-blue-600 hover:underline">
              https://aistudio.google.com/app/apikey
            </a>
            에 접속합니다.
          </Step>
          <Step number={2} title="API 키 생성">
            "Create API Key" 버튼을 클릭하여 새 API 키를 생성합니다.
          </Step>
          <Step number={3} title=".env 파일 수정">
            <code className="block bg-gray-100 p-3 rounded mt-2 text-sm">
              # backend/.env<br/>
              GOOGLE_API_KEY=생성된_API_키
            </code>
          </Step>
          <Step number={4} title="서버 재시작">
            백엔드 서버를 재시작합니다 (Ctrl+C 후 다시 실행).
          </Step>
        </div>

        <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
          <strong>💡 팁:</strong> 여러 API 키를 콤마로 구분하여 등록하면,
          한도 초과 시 자동으로 다음 키로 전환됩니다.
          <code className="block bg-amber-100 p-2 rounded mt-2">
            GOOGLE_API_KEYS=키1,키2,키3
          </code>
        </div>
      </div>

      <div>
        <h4 className="text-lg font-semibold mb-3">Naver API 설정</h4>
        <p className="text-gray-600 mb-4">
          과거 뉴스 검색 기능을 사용하려면 Naver 검색 API가 필요합니다.
        </p>

        <div className="space-y-4">
          <Step number={1} title="네이버 개발자 센터 접속">
            <a href="https://developers.naver.com/apps" target="_blank" rel="noopener noreferrer"
               className="text-blue-600 hover:underline">
              https://developers.naver.com/apps
            </a>
            에 접속합니다.
          </Step>
          <Step number={2} title="애플리케이션 등록">
            새 애플리케이션을 등록하고 "검색" API를 선택합니다.
          </Step>
          <Step number={3} title=".env 파일 수정">
            <code className="block bg-gray-100 p-3 rounded mt-2 text-sm">
              # backend/.env<br/>
              NAVER_CLIENT_ID=발급받은_클라이언트_ID<br/>
              NAVER_CLIENT_SECRET=발급받은_시크릿
            </code>
          </Step>
          <Step number={4} title="서버 재시작">
            백엔드 서버를 재시작합니다.
          </Step>
        </div>
      </div>
    </div>
  );
}

function AIGuideSection() {
  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-lg font-semibold mb-3">AI 필터링이란?</h4>
        <p className="text-gray-600 leading-relaxed">
          Google Gemini AI를 사용하여 뉴스 기사가 유튜브 콘텐츠로 적합한지 자동으로 분석합니다.
          단순 실적 발표가 아닌, 스토리가 있는 기사를 찾아줍니다.
        </p>
      </div>

      <div>
        <h4 className="text-lg font-semibold mb-3">분석 결과 해석</h4>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">AI: 85</span>
            <div>
              <p className="font-medium text-sm">AI 점수 (0-100)</p>
              <p className="text-xs text-gray-500">높을수록 유튜브 콘텐츠에 적합</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs font-medium">Fail</span>
            <div>
              <p className="font-medium text-sm">카테고리</p>
              <p className="text-xs text-gray-500">Fail(실패) / Success(성공) / Comeback(부활)</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs font-medium">YT: 높음</span>
            <div>
              <p className="font-medium text-sm">유튜브 적합도</p>
              <p className="text-xs text-gray-500">높음 / 중간 / 낮음</p>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h4 className="text-lg font-semibold mb-3">AI 분석 사용법</h4>
        <div className="space-y-2 text-gray-600">
          <p><strong>개별 분석:</strong> 뉴스 카드의 ✨ 아이콘 클릭</p>
          <p><strong>일괄 분석:</strong> 상단 "AI Filter" 버튼 클릭 → 프리셋 선택 → 분석 실행</p>
        </div>
      </div>

      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        <strong>💡 무료 사용량:</strong> Gemini Flash 모델은 하루 1,500회까지 무료입니다.
        여러 API 키를 등록하면 한도를 늘릴 수 있습니다.
      </div>
    </div>
  );
}

function PresetGuideSection() {
  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-lg font-semibold mb-3">프리셋이란?</h4>
        <p className="text-gray-600 leading-relaxed">
          프리셋은 자주 사용하는 필터 조건을 저장해둔 것입니다.
          클릭 한 번으로 관련 뉴스만 필터링할 수 있습니다.
        </p>
      </div>

      <div>
        <h4 className="text-lg font-semibold mb-3">기본 프리셋</h4>
        <div className="space-y-3">
          <PresetItem
            name="브랜드 몰락"
            keywords={['파산', '폐업', '몰락', '위기', '적자', '실패']}
            description="기업/브랜드 실패 스토리 검색"
          />
          <PresetItem
            name="브랜드 성공"
            keywords={['성공', '흥행', '대박', '성장', '확장', '1위']}
            description="성공 스토리, 히트 상품 검색"
          />
          <PresetItem
            name="부활 스토리"
            keywords={['부활', '재기', '턴어라운드', '회복', '흑자전환']}
            description="위기 극복, 반등 스토리 검색"
          />
          <PresetItem
            name="프랜차이즈"
            keywords={['프랜차이즈', '가맹점', '치킨', '커피', '편의점']}
            description="프랜차이즈 관련 뉴스 검색"
          />
          <PresetItem
            name="스타트업"
            keywords={['스타트업', '유니콘', '투자유치', '벤처', 'IPO']}
            description="스타트업, 벤처 뉴스 검색"
          />
        </div>
      </div>

      <div>
        <h4 className="text-lg font-semibold mb-3">프리셋 관리</h4>
        <ul className="space-y-2 text-gray-600 text-sm">
          <li>• <strong>추가:</strong> "+ Add" 버튼으로 새 프리셋 생성</li>
          <li>• <strong>수정:</strong> 프리셋 옆 ✏️ 아이콘 클릭</li>
          <li>• <strong>삭제:</strong> 프리셋 옆 🗑️ 아이콘 클릭</li>
          <li>• <strong>적용:</strong> 프리셋 이름 클릭</li>
        </ul>
      </div>
    </div>
  );
}

function SearchGuideSection() {
  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-lg font-semibold mb-3">네이버 뉴스 검색</h4>
        <div className="border rounded-lg p-4">
          <h5 className="font-medium mb-2">🔍 네이버 검색 (Search)</h5>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• 키워드로 뉴스 검색</li>
            <li>• 과거 뉴스까지 검색 가능</li>
            <li>• 언론사별 필터링 지원</li>
            <li>• 최대 1,000개 결과</li>
            <li>• Naver API 키 필요</li>
          </ul>
        </div>
      </div>

      <div>
        <h4 className="text-lg font-semibold mb-3">검색 사용법</h4>
        <ol className="space-y-2 text-gray-600">
          <li className="flex gap-2">
            <span className="flex-shrink-0 w-6 h-6 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-sm font-medium">1</span>
            <span>헤더의 초록색 <strong>Search</strong> 버튼 클릭</span>
          </li>
          <li className="flex gap-2">
            <span className="flex-shrink-0 w-6 h-6 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-sm font-medium">2</span>
            <span>검색어 입력 (예: "스타벅스 폐점", "치킨 프랜차이즈 위기")</span>
          </li>
          <li className="flex gap-2">
            <span className="flex-shrink-0 w-6 h-6 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-sm font-medium">3</span>
            <span>최대 결과 수 선택</span>
          </li>
          <li className="flex gap-2">
            <span className="flex-shrink-0 w-6 h-6 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-sm font-medium">4</span>
            <span><strong>검색 및 저장</strong> 버튼 클릭</span>
          </li>
        </ol>
      </div>

      <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
        <strong>💡 팁:</strong> 검색 결과는 자동으로 DB에 저장되어
        프리셋 필터나 AI 분석에 활용할 수 있습니다.
      </div>
    </div>
  );
}

function ShortcutsSection() {
  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-lg font-semibold mb-3">화면 단축키</h4>
        <p className="text-gray-600 mb-4">
          (추후 구현 예정)
        </p>
        <div className="space-y-2">
          <ShortcutItem keys={['?']} description="도움말 열기" />
          <ShortcutItem keys={['Esc']} description="모달 닫기" />
          <ShortcutItem keys={['R']} description="뉴스 새로고침" />
          <ShortcutItem keys={['/']} description="검색창 포커스" />
        </div>
      </div>

      <div>
        <h4 className="text-lg font-semibold mb-3">뉴스 카드</h4>
        <div className="space-y-2">
          <ShortcutItem keys={['Click']} description="원문 링크 열기" />
          <ShortcutItem keys={['⭐']} description="북마크 토글" />
          <ShortcutItem keys={['✨']} description="AI 분석 실행" />
          <ShortcutItem keys={['☑️']} description="선택/해제" />
        </div>
      </div>
    </div>
  );
}

// Helper Components
function FeatureItem({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex items-start gap-3">
      <ChevronRight className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
      <div>
        <p className="font-medium text-sm">{title}</p>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
    </div>
  );
}

function Step({ number, title, children }: { number: number; title: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-3">
      <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">
        {number}
      </span>
      <div>
        <p className="font-medium text-sm">{title}</p>
        <div className="text-sm text-gray-600">{children}</div>
      </div>
    </div>
  );
}

function PresetItem({ name, keywords, description }: { name: string; keywords: string[]; description: string }) {
  return (
    <div className="border rounded-lg p-3">
      <p className="font-medium text-sm mb-1">{name}</p>
      <p className="text-xs text-gray-500 mb-2">{description}</p>
      <div className="flex flex-wrap gap-1">
        {keywords.slice(0, 5).map((kw) => (
          <span key={kw} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
            {kw}
          </span>
        ))}
        {keywords.length > 5 && (
          <span className="text-xs text-gray-400">+{keywords.length - 5}</span>
        )}
      </div>
    </div>
  );
}

function ShortcutItem({ keys, description }: { keys: string[]; description: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b last:border-0">
      <span className="text-sm text-gray-600">{description}</span>
      <div className="flex gap-1">
        {keys.map((key) => (
          <kbd key={key} className="px-2 py-1 bg-gray-100 border rounded text-xs font-mono">
            {key}
          </kbd>
        ))}
      </div>
    </div>
  );
}
