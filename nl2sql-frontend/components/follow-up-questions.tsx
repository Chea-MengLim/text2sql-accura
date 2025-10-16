'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, ArrowRight } from 'lucide-react';

interface FollowUpQuestionsProps {
  questions: string[];
  onQuestionClick: (question: string) => void;
}

export function FollowUpQuestions({ questions, onQuestionClick }: FollowUpQuestionsProps) {
  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <Card className="border-dashed border-2 border-blue-200 bg-blue-50/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2 text-blue-700">
          <MessageSquare className="h-5 w-5" />
          Suggested Follow-up Questions
        </CardTitle>
        <CardDescription className="text-blue-600">
          Click on any question below to explore your data further
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {questions.map((question, index) => (
          <div key={index} className="group">
            <Button
              variant="outline"
              className="w-full justify-start text-left h-auto p-4 border-blue-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 group-hover:shadow-sm"
              onClick={() => onQuestionClick(question)}
            >
              <div className="flex items-start gap-3 w-full">
                <Badge 
                  variant="secondary" 
                  className="flex-shrink-0 mt-0.5 bg-blue-100 text-blue-700 border-blue-200"
                >
                  {index + 1}
                </Badge>
                <span className="flex-1 text-sm leading-relaxed text-gray-700 group-hover:text-blue-700 transition-colors">
                  {question}
                </span>
                <ArrowRight className="h-4 w-4 flex-shrink-0 text-gray-400 group-hover:text-blue-500 transition-colors" />
              </div>
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
