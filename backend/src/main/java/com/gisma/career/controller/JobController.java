package com.gisma.career.controller;

import com.gisma.career.dto.JobResponse;
import com.gisma.career.model.Student;
import com.gisma.career.service.JobRecommendationService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/jobs")
public class JobController {

    private final JobRecommendationService jobService;

    public JobController(JobRecommendationService jobService) {
        this.jobService = jobService;
    }

    /**
     * Get recommended jobs for the logged-in student.
     * Optional ?filter=all|internship|fulltime|parttime|remote
     */
    @GetMapping("/recommended")
    public ResponseEntity<List<JobResponse>> recommended(@AuthenticationPrincipal Student student,
                                                         @RequestParam(required = false, defaultValue = "all") String filter) {
        return ResponseEntity.ok(jobService.recommendFor(student, filter));
    }
}
