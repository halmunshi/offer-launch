import { useReducer } from "react";

type OnboardingState<TAnswers extends Record<string, unknown>> = {
  currentStep: number;
  answers: TAnswers;
  direction: 1 | -1;
  totalSteps: number;
};

type OnboardingAction<TAnswers extends Record<string, unknown>> =
  | { type: "NEXT" }
  | { type: "BACK" }
  | { type: "SET_ANSWER"; key: keyof TAnswers; value: TAnswers[keyof TAnswers] }
  | { type: "RESET"; payload: TAnswers };

function reducer<TAnswers extends Record<string, unknown>>(
  state: OnboardingState<TAnswers>,
  action: OnboardingAction<TAnswers>,
): OnboardingState<TAnswers> {
  switch (action.type) {
    case "NEXT": {
      return {
        ...state,
        currentStep: Math.min(state.currentStep + 1, state.totalSteps - 1),
        direction: 1,
      };
    }
    case "BACK": {
      return {
        ...state,
        currentStep: Math.max(state.currentStep - 1, 0),
        direction: -1,
      };
    }
    case "SET_ANSWER": {
      return {
        ...state,
        answers: {
          ...state.answers,
          [action.key]: action.value,
        },
      };
    }
    case "RESET": {
      return {
        currentStep: 0,
        answers: action.payload,
        direction: 1,
        totalSteps: state.totalSteps,
      };
    }
    default:
      return state;
  }
}

export function useOnboarding<TAnswers extends Record<string, unknown>>({
  totalSteps,
  initialAnswers,
}: {
  totalSteps: number;
  initialAnswers: TAnswers;
}) {
  const [state, dispatch] = useReducer(reducer<TAnswers>, {
    currentStep: 0,
    answers: initialAnswers,
    direction: 1,
    totalSteps,
  });

  return {
    currentStep: state.currentStep,
    answers: state.answers,
    direction: state.direction,
    totalSteps: state.totalSteps,
    next: () => dispatch({ type: "NEXT" }),
    back: () => dispatch({ type: "BACK" }),
    setAnswer: <K extends keyof TAnswers>(key: K, value: TAnswers[K]) => {
      dispatch({ type: "SET_ANSWER", key, value });
    },
    reset: () => dispatch({ type: "RESET", payload: initialAnswers }),
    isFirst: state.currentStep === 0,
    isLast: state.currentStep === state.totalSteps - 1,
    progress: Math.floor((state.currentStep / state.totalSteps) * 100),
  };
}
