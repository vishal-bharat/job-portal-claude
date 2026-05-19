package com.gisma.career.controller;

import com.gisma.career.dto.ProfileResponse;
import com.gisma.career.dto.SkillRequest;
import com.gisma.career.model.Skill;
import com.gisma.career.model.Student;
import com.gisma.career.service.SkillService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/skills")
public class SkillController {

    private final SkillService skillService;

    public SkillController(SkillService skillService) {
        this.skillService = skillService;
    }

    /** Public: list of all skills in the catalog (used for "Suggested Skills"). */
    @GetMapping("/all")
    public ResponseEntity<List<String>> allSkills() {
        return ResponseEntity.ok(skillService.allSkills().stream().map(Skill::getName).toList());
    }

    /** My current skills. */
    @GetMapping("/me")
    public ResponseEntity<List<String>> mySkills(@AuthenticationPrincipal Student student) {
        return ResponseEntity.ok(student.getSkills().stream().map(Skill::getName).sorted().toList());
    }

    @PostMapping("/me")
    public ResponseEntity<ProfileResponse> addSkill(@AuthenticationPrincipal Student student,
                                                    @Valid @RequestBody SkillRequest req) {
        Student updated = skillService.addSkillToStudent(student, req.getName());
        return ResponseEntity.ok(ProfileResponse.fromEntity(updated));
    }

    @DeleteMapping("/me/{name}")
    public ResponseEntity<ProfileResponse> removeSkill(@AuthenticationPrincipal Student student,
                                                       @PathVariable String name) {
        Student updated = skillService.removeSkillFromStudent(student, name);
        return ResponseEntity.ok(ProfileResponse.fromEntity(updated));
    }
}
